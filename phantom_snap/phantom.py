#!/usr/bin/env python

import eventlet
from eventlet.green import subprocess
from eventlet.green import threading
from eventlet.timeout import Timeout
from eventlet.queue import Queue, Empty

import copy
import json
import os
import base64
import traceback
import time
import renderer
import logging

from signal import *
from settings import PHANTOMJS, merge


class PhantomJSRenderer(renderer.Renderer):
    """
    Render a web page to an image, using either a URL or raw HTML.

    Requires PhantomJS to be installed on the host: http://phantomjs.org/
    """

    def __init__(self, config, logger=None, register_shutdown=False):

        self.config = copy.deepcopy(PHANTOMJS)
        self.config = merge(self.config, config)

        self._proc = None
        self._stderr_reader = None
        self._comms_lock = threading.RLock()
        self._shutdown_lock = threading.RLock()

        if not self._which(self.config[u'executable']):
            raise renderer.RenderError(''.join([u"Can't locate PhantomJS executable: ", self.config[u'executable']]))

        if not os.path.isfile(self.config[u'script']):
            raise renderer.RenderError(''.join([u"Can't locate script: ", self.config[u'script']]))

        if logger is not None:
            self._logger = logger
        else:
            self._logger = logging.getLogger(u'PhantomJSRenderer')

        if register_shutdown and isinstance(threading.current_thread(), threading._MainThread):
            for sig in (SIGABRT, SIGINT, SIGTERM):
                signal(sig, self._on_signal)

    def get_config(self):
        return self.config

    def render(self, url, html=None, img_format=u'PNG', width=1280, height=1024, page_load_timeout=None, user_agent=None,
               headers=None, cookies=None, html_encoding=u'utf-8'):
        """
        Render a URL target or HTML to an image file.
        :param url:
        :param html:
        :param img_format:
        :param width:
        :param height:
        :param page_load_timeout:
        :param user_agent:
        :param headers:
        :param cookies:
        :param html_encoding:
        :return:
        """

        request = {u'url': url, u'width': width, u'height': height, u'format': img_format}

        if html is not None:
            if isinstance(html, unicode):
                html = html.encode(html_encoding, errors='replace')

            b64 = base64.b64encode(html)
            request[u'html64'] = b64

        if user_agent is not None:
            request[u'userAgent'] = user_agent

        if headers is not None:
            request[u'headers'] = headers

        if cookies is not None:
            request[u'cookies'] = cookies

        with self._comms_lock:
            try:
                first_render = False

                if not hasattr(self, '_proc') or self._proc is None:
                    startup_timeout = self.config[u'timeouts'][u'process_startup']

                    command = self._construct_command()

                    self._logger.info(u"Starting the PhantomJS process: " + u" ".join(command))

                    with Timeout(startup_timeout):
                        self._proc = subprocess.Popen(command,
                                                      bufsize=4096,
                                                      shell=False,
                                                      stdin=subprocess.PIPE,
                                                      stdout=subprocess.PIPE,
                                                      stderr=subprocess.PIPE,
                                                      env=self.config[u'env'])

                        self._stderr_reader = PipeReader(self._proc.stderr)

                    first_render = True

                render_timeout = self.config[u'timeouts'][u'render_response']

                if page_load_timeout is None:
                    if first_render:
                        page_load_timeout = self.config[u'timeouts'][u'initial_page_load']
                    else:
                        page_load_timeout = self.config[u'timeouts'][u'page_load']

                request[u'timeout'] = page_load_timeout * 1000  # Convert seconds to ms

                request_string = json.dumps(request)

                try:
                    with Timeout(page_load_timeout + render_timeout):

                        self._logger.debug(u'Sending request: ' + request_string)
                        self._proc.stdin.write(request_string + '\n')
                        self._proc.stdin.flush()

                        response_string = self._proc.stdout.readline()

                except Timeout:
                    response_string = None
                    self._logger.warn(u'Received no response, terminating PhantomJS.')
                    self.shutdown()

                err_messages = self._check_stderr()

                if err_messages is not None and self._logger.isEnabledFor(logging.DEBUG):
                    self._logger.debug(err_messages)

                response = {u'url': url,
                            u'status': None,
                            u'load_time': None,
                            u'paint_time': None,
                            u'base64': None,
                            u'format': img_format,
                            u'error': None}

                if response_string is None:
                    response[u'status'] = u'fail'
                    response[u'error'] = u'Render request has timed out.'
                else:
                    try:
                        phantom_response = json.loads(response_string)

                        if self._logger.isEnabledFor(logging.DEBUG):
                            msg = {}
                            msg.update(phantom_response)
                            msg[u'base64'] = u'<omitted>'
                            self._logger.debug(u'Received response: ' + json.dumps(msg))

                        if u'status' in phantom_response:
                            response[u'status'] = phantom_response[u'status']
                        else:
                            response[u'status'] = u'fail'

                        if u'loadTime' in phantom_response:
                            response[u'load_time'] = phantom_response[u'loadTime']

                        if u'paintTime' in phantom_response:
                            response[u'paint_time'] = phantom_response[u'paintTime']

                        if u'base64' in phantom_response:
                            response[u'base64'] = phantom_response[u'base64']

                        if u'error' in phantom_response:
                            response[u'error'] = json.dumps(phantom_response[u'error'])
                        elif err_messages is not None:
                            response[u'error'] = err_messages

                    except (ValueError, KeyError) as e:
                        self._logger.debug(u'Error parsing response: {}\nTerminating PhantomJS.\n{}'.format(response_string, traceback.format_exc()))

                        self.shutdown()

                        response[u'status'] = u'fail'
                        response[u'error'] = ''.join([str(e), u'\nPhantomJS response: ', response_string])

                return response

            except (Timeout, Exception):
                self._logger.error(u'Unexpected error, terminating PhantomJS.\n' + traceback.format_exc())
                self.shutdown()
                raise

    def shutdown(self, timeout=None):
        """

        :return:
        """
        with self._shutdown_lock:
            if hasattr(self, '_proc') and self._proc is not None:
                try:
                    self._proc.kill()
                    self._proc.wait()
                finally:
                    del self._proc

                self._logger.info(u'PhantomJS terminated.')

        if self._stderr_reader is not None:
            self._stderr_reader.shutdown()

    def _check_stderr(self):
        """Collect any input from the stderr pipe and return it."""

        err = self._stderr_reader.get()
        err_messages = []

        while err is not None:
            err_messages.append(err.decode('UTF-8', errors='replace'))
            err = self._stderr_reader.get()

        if len(err_messages) > 0:
            return u'\n'.join(err_messages)
        else:
            return None

    def _on_signal(self, sig, frame):
        """"""
        self.shutdown()
        os._exit(0)

    def _construct_command(self):
        """Build the command array for executing the PhantomJS process."""

        executable = self._which(self.config[u'executable'])

        return [executable] + self.config[u'args'] + [self.config[u'script']]

    @staticmethod
    def _which(program):
        """Locate the executable on the path if required."""

        def is_exe(fpath):
            return os.path.isfile(fpath) and os.access(fpath, os.X_OK)

        fpath, fname = os.path.split(program)
        if fpath:
            if is_exe(program):
                return program
        else:
            for path in os.environ["PATH"].split(os.pathsep):
                path = path.strip('"')
                exe_file = os.path.join(path, program)
                if is_exe(exe_file):
                    return exe_file

        return None


class PipeReader:

    def __init__(self, pipe):

        self._pipe = pipe
        self._queue = Queue()

        _queue = self._queue

        def _enqueue_output():
            for line in iter(pipe.readline, b''):
                _queue.put(line)

            pipe.close()

        self._green_thread = eventlet.spawn(_enqueue_output)

    def get(self):
        try:
            return self._queue.get_nowait()
        except Empty:
            pass
        return None

    def shutdown(self):

        if self._green_thread is not None:
            try:
                self._green_thread.kill()
            except:
                pass
