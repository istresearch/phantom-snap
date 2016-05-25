#!/usr/bin/env python

# Render a web page to an image, using either a URL or raw HTML.
#
# Requires PhantomJS to be installed on the host: http://phantomjs.org/

import copy
import json
import os
import subprocess
import traceback
import renderer
import logging

from signal import *
from settings import PHANTOMJS
from threadtools import TimedMethod
from threadtools import TimedRLock


class PhantomJSRenderer(renderer.Renderer):

    def __init__(self, config):

        self.config = copy.deepcopy(PHANTOMJS)
        self.config.update(config)

        self._proc = None
        self._comms_lock = TimedRLock()

        if not self._which(self.config[u'executable']):
            raise renderer.RenderError(''.join([u"Can't locate PhantomJS executable: ", self.config[u'executable']]))

        if not os.path.isfile(self.config[u'script']):
            raise renderer.RenderError(''.join([u"Can't locate script: ", self.config[u'script']]))

        self._logger = logging.getLogger(u'PhantomJSRenderer')

        for sig in (SIGABRT, SIGINT, SIGTERM):
            signal(sig, self._on_signal)

    def render(self, url, html=None, img_format=u'PNG', width=1280, height=1024, page_load_timeout=None, user_agent=None,
               headers=None, cookies=None):
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
        :return:
        """

        request = {u'url': url, u'width': width, u'height': height, u'format': img_format}

        if html is not None:
            request[u'html'] = html

        if page_load_timeout is None:
            page_load_timeout = self.config[u'timeouts'][u'page_load']

        if user_agent is not None:
            request[u'userAgent'] = user_agent

        if headers is not None:
            request[u'headers'] = headers

        if cookies is not None:
            request[u'cookies'] = cookies

        request[u'timeout'] = page_load_timeout * 1000  # Convert seconds to ms

        with self._comms_lock:
            try:
                first_render = False

                if self._proc is None:
                    startup_timeout = self.config[u'timeouts'][u'process_startup']

                    command = self._construct_command()
                    kwargs = {u'shell': False,
                              u'stdin': subprocess.PIPE,
                              u'stdout': subprocess.PIPE,
                              u'stderr': subprocess.STDOUT,
                              u'env': self.config[u'env']
                              }

                    self._logger.debug(u'Starting the PhantomJS process: ' + ' '.join(command))
                    self._proc = TimedMethod().call(startup_timeout, subprocess.Popen, (command,), kwargs, join=True)

                    first_render = True

                request_string = json.dumps(request);

                self._logger.debug(u'Sending request: ' + request_string)
                self._proc.stdin.write(request_string + '\n')
                self._proc.stdin.flush()

                render_timeout = self.config[u'timeouts'][u'render_response']

                if first_render:
                    render_timeout = self.config[u'timeouts'][u'initial_render_response']

                response_string = TimedMethod().call(page_load_timeout + render_timeout, self._proc.stdout.readline)

                response = {u'url': url, u'status': None, u'load_time': None, u'base64': None, u'format': img_format, u'error': None}

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

                        if u'base64' in phantom_response:
                            response[u'base64'] = phantom_response[u'base64']

                        if u'error' in phantom_response:
                            response[u'error'] = phantom_response[u'error']

                    except Exception as e:
                        self._logger.debug(u'Error parsing response, terminating PhantomJS.\n' + traceback.format_exc())
                        self.shutdown()

                        response[u'status'] = u'fail'
                        response[u'error'] = ''.join([str(e), u'\nPhantomJS response: ', response_string])

                return response

            except Exception:
                self._logger.error(u'Unexpected error, terminating PhantomJS.\n' + traceback.format_exc())
                self.shutdown()
                raise

    def shutdown(self, timeout=None):
        """ Shutdown the PhantomJS process.
        :param timeout:
        :return:
        """

        # Attempt to acquire the communications lock while we shutdown the
        # process cleanly.
        if self._comms_lock.acquire(True, timeout):
            try:
                if self._proc is None:
                    return

                try:
                    self._proc.stdin.write('exit\n')
                    self._proc.stdin.flush()

                    # Wait for PhantomJS to exit
                    TimedMethod().call(1, self._proc.wait)
                except:
                    pass  # eat it
                finally:
                    code = self._proc.poll()

                    if code is None:
                        self._proc.terminate()
                    else:
                        self._logger.info(''.join([u'PhantomJS exit code ', str(code)]))

                    self._proc = None
            finally:
                self._comms_lock.release()
        else:
            # Didn't get the comms lock within our timeout, so double-tap to
            # the head. The reason for this could be we either don't care
            # about a pending result (intentionally short timeout), the
            # shutdown timeout was too short to receive a pending response,
            # or we have a stuck PhantomJS process.
            proc = self._proc
            self._proc = None

            if proc is not None:
                proc.kill()

    def _on_signal(self, sig, frame):
        """"""
        self.shutdown(timeout=0)
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
