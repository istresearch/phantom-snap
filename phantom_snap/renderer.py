
import abc


class Renderer(object):
    __metaclass__ = abc.ABCMeta

    @abc.abstractmethod
    def render(self, url, html=None, img_format='PNG', width=1280, height=1024, page_load_timeout=None, user_agent=None,
               headers=None, cookies=None):
        raise NotImplementedError('users must define render to use this base class')


class RenderError(Exception):
    """Exception raised for errors during rendering.

    Attributes:
        msg  -- explanation of the error
    """
    def __init__(self, msg, *args, **kwargs):
        self.msg = msg

    def __str__(self):
        return repr(self.msg)