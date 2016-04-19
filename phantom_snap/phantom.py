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
from settings import PHANTOMJS
from threadtools import TimedMethod
from threadtools import TimedRLock


class PhantomJSRenderer(renderer.Renderer):
    def __init__(self, config):

        self.config = copy.deepcopy(PHANTOMJS)
        self.config.update(config)

        self._proc = None
        self._comms_lock = TimedRLock()

        if not os.path.isfile(self.config['executable']):
            raise renderer.RenderError(''.join(["Can't locate PhantomJS executable: ", self.config['executable']]))

        if not os.path.isfile(self.config['script']):
            raise renderer.RenderError(''.join(["Can't locate script: ", self.config['script']]))

    def render(self, url, html=None, img_format='PNG', width=1280, height=1024, page_load_timeout=None, user_agent=None,
               headers=None, cookies=None):

        request = {'url': url, 'width': width, 'height': height, 'format': img_format}

        if html is not None:
            request['html'] = html

        if page_load_timeout is None:
            page_load_timeout = self.config['timeouts']['page_load']

        if user_agent is not None:
            request['userAgent'] = user_agent

        if headers is not None:
            request['headers'] = headers

        if cookies is not None:
            request['cookies'] = cookies

        request['timeout'] = page_load_timeout * 1000  # Convert seconds to ms

        with self._comms_lock:
            try:
                first_render = False

                if self._proc is None:
                    startup_timeout = self.config['timeouts']['process_startup']

                    command = self._construct_command()
                    kwargs = {'shell': False,
                              'stdin': subprocess.PIPE,
                              'stdout': subprocess.PIPE,
                              'stderr': subprocess.STDOUT,
                              'env': self.config['env']
                              }

                    self._proc = TimedMethod().call(startup_timeout, subprocess.Popen, (command,), kwargs, join=True)

                    first_render = True

                self._proc.stdin.write(json.dumps(request) + '\n')
                self._proc.stdin.flush()

                render_timeout = self.config['timeouts']['render_response']

                if first_render:
                    render_timeout = self.config['timeouts']['initial_render_response']

                response_string = TimedMethod().call(page_load_timeout + render_timeout, self._proc.stdout.readline)

                response = {'url': url, 'status': None, 'load_time': None, 'base64': None, 'format': img_format, 'error': None}

                if response_string is None:
                    response['status'] = 'fail'
                    response['error'] = 'Render request has timed out.'
                else:
                    try:
                        phantom_reponse = json.loads(response_string)

                        if 'status' in phantom_reponse:
                            response['status'] = phantom_reponse['status']
                        else:
                            response['status'] = 'fail'

                        if 'loadTime' in phantom_reponse:
                            response['load_time'] = phantom_reponse['loadTime']

                        if 'base64' in phantom_reponse:
                            response['base64'] = phantom_reponse['base64']

                        if 'error' in phantom_reponse:
                            response['error'] = phantom_reponse['error']

                    except Exception as e:
                        self.shutdown()
                        response['status'] = 'fail'
                        response['error'] = ''.join([str(e), '\nPhantomJS response: ', response_string])

                return response
            except Exception as e:
                traceback.print_exc()
                print 'Unexpected error, terminating PhantomJS: ' + str(e)
                self.shutdown()

    def _construct_command(self):
        return [self.config['executable']] + self.config['args'] + [self.config['script']]

    def shutdown(self, timeout=None):

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
                        self._proc.kill()
                    else:
                        print ''.join(['PhantomJS exit code ', str(code)])  # TODO Logging?

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
            proc.kill()
