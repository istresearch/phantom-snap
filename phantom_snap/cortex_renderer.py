from .renderer import Renderer
import requests
from requests.exceptions import RequestException, \
                                ConnectionError, \
                                Timeout, \
                                TooManyRedirects
import base64
import copy
import logging
from .settings import CORTEX, merge
import traceback
import time

class CortexRenderer(Renderer):
    """Offloads the rendering process to a PhantomJSRenderer
    running inside of Cortex cluster  """

    def __init__(self, config, logger=None):

        # Load the config
        self.config = copy.deepcopy(CORTEX)
        self.config = merge(self.config, config)

        if logger is not None:
            self._logger = logger
        else:
            self._logger = logging.getLogger(u'CortexRenderer')

    def get_config(self):
        """ Return the configuration dictionary.
        :return: dict
        """
        return self.config

    def is_base64(self, the_string):
        try:
            byte_data = the_string

            if isinstance(the_string, str):
                byte_data = the_string.encode('utf-8', errors='ignore')

            return base64.b64encode(base64.b64decode(byte_data)) == byte_data
        except Exception:
            return False

    def _prep_json(self, url, html, img_format, width, height, page_load_timeout,
                   user_agent, headers, cookies, html_encoding, http_proxy):
        """Preps the json value to be passed to the request"""
        json_dict = {
        # non-None args
            'url': url,
            'img_format': img_format,
            'width': width,
            'height': height,
            'html_encoding': html_encoding
        }

        # args that can be None
        if html is not None:
            # accept both text and base64 encoded text
            if self.is_base64(html):
                json_dict['html'] = html
            else:
                json_dict['html'] = base64.b64encode(html.encode(html_encoding, errors='ignore')).decode('utf-8')

        if page_load_timeout is not None:
            json_dict['page_load_timeout'] = page_load_timeout

        if user_agent is not None:
            json_dict['user_agent'] = user_agent

        if http_proxy is not None:
            json_dict['http_proxy'] = http_proxy

        if headers is not None:
            json_dict['headers'] = headers

        if cookies is not None:
            json_dict['cookies'] = cookies

        return json_dict

    def _prep_headers(self):
        """Preps the headers to send to cortex"""
        h_dict = {
            'content-type': 'application/json'
        }

        if 'api_key' in self.config and \
                self.config['api_key'] is not None:
            h_dict['x-api-key'] = self.config['api_key']

        return h_dict

    def _prep_timeout(self):
        """Preps the request timeout to cortex"""
        return self.config['timeouts']['request_timeout']

    def render(self, url, html=None, img_format='PNG', width=1280, height=1024,
               page_load_timeout=None, user_agent=None,
               headers=None, cookies=None, html_encoding=u'utf-8', http_proxy=None):
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
        :return dict:
        """
        # prep request
        json_dict = self._prep_json(url=url,
                                    html=html,
                                    img_format=img_format,
                                    width=width,
                                    height=height,
                                    page_load_timeout=page_load_timeout,
                                    user_agent=user_agent,
                                    headers=headers,
                                    cookies=cookies,
                                    html_encoding=html_encoding,
                                    http_proxy=http_proxy)
        request_headers = self._prep_headers()
        timeout = self._prep_timeout()

        # send it
        try:
            self._logger.info("Sending cortex request {} {} {} {}".format(url, json_dict, request_headers, timeout))
            start_time = time.time()
            result = requests.post(url=self.config['url'],
                                   json=json_dict,
                                   headers=request_headers,
                                   allow_redirects=True,
                                   timeout=timeout)
            self._logger.info("Request took {}s".format(time.time() - start_time))

            # valid response should be json
            json_result = result.json()
            json_copy = copy.deepcopy(json_result)
            if 'base64' in json_copy and json_copy['base64'] is not None:
                json_copy['base64'] = '<omitted>'
            self._logger.debug("Received data from cortex {}".format(json_copy))
        except (ValueError, ConnectionError, Timeout,
                TooManyRedirects, RequestException) as e:
            self._logger.error("Exception while calling cortex {}".format(traceback.format_exc()))
            return {
                u'url': url,
                u'status': u'fail',
                u'load_time': None,
                u'paint_time': None,
                u'base64': None,
                u'format': img_format,
                u'error': traceback.format_exc(),
            }

        # handle error within cortex instance function
        if result.status_code != 200:
            self._logger.warning("Received unexpected {} status code from cortex".format(result.status_code))
            response = {
                u'url': url,
                u'status': u'fail',
                u'load_time': None,
                u'paint_time': None,
                u'base64': None,
                u'format': img_format,
                u'error': None
            }

            if 'message' in json_result:
                response['error'] = json_result['ex'] if 'ex' in json_result else json_result['message']
            return response

        return json_result

    def shutdown(self, timeout=None):
        pass
