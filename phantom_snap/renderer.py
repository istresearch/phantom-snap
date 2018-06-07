
import abc


class Renderer(object):
    __metaclass__ = abc.ABCMeta

    @abc.abstractmethod
    def get_config(self):
        """ Return the configuration dictionary.
        :return: dict
        """
        raise NotImplementedError('Users must implement get_config() to use this base class')

    @abc.abstractmethod
    def render(self, url, html=None, img_format='PNG', width=1280, height=1024, page_load_timeout=None, user_agent=None,
               headers=None, cookies=None, html_encoding=u'utf-8'):
        raise NotImplementedError('Users must implement render() to use this base class')

    @abc.abstractmethod
    def shutdown(self, timeout=None):
        """ Shutdown and cleanup the renderer.
        :param timeout: Time in seconds to wait for shutdown.
        :return:
        """
        raise NotImplementedError('Users must implement shutdown() to use this base class')


class RenderError(Exception):
    """Exception raised for errors during rendering.

    Attributes:
        msg  -- explanation of the error
    """
    def __init__(self, msg, *args, **kwargs):
        self.msg = msg

    def __str__(self):
        return repr(self.msg)