
import copy
from renderer import Renderer
import logging
import threading
import time

from settings import LIFETIME
from threadtools import Thread


class Lifetime(Renderer):
    """
    Wraps a Renderer instance and limits the maximum time a single render
    instance can live, and also shuts down a process if it has been unused for
    a specified time period.

    PhantomJS can be configured to use an in-memory browser cache which can
    grow without bounds. The Lifetime decorator is useful for controlling this
    growth by limiting the amount of time a single Renderer can live, and
    releasing its accumulated resources.

    For long or continual running of the rendering process, it is highly
    recommended to wrap the Renderer with the Lifetime decorator to prevent
    eventual OOM.
    """

    _delegate = None
    _last_render_time = None
    _start_time = None

    _running = False
    _thread = None
    _condition = threading.Condition(threading.RLock())
    _lock = threading.RLock()

    def __init__(self, renderer):

        self._delegate = renderer
        self.config = copy.deepcopy(LIFETIME)
        self.config.update(renderer.get_config())

        self._logger = logging.getLogger(u'LifetimeDecorator')

    def get_config(self):
        return self.config

    def render(self, url, html=None, img_format='PNG', width=1280, height=1024, page_load_timeout=None, user_agent=None,
               headers=None, cookies=None):

        with self._lock:
            self._last_render_time = time.time()

            if self._start_time is None:
                self._start_time = self._last_render_time

            if not self._running:
                self._startup()

            self._delegate.render(url, html, img_format, width, height, page_load_timeout, user_agent, headers, cookies)

    def _startup(self):

        self._running = True
        self._thread = Thread(target=self._lifetime_monitor)
        self._thread.daemon = True
        self._thread.start()

    def shutdown(self, timeout=None):

        self._running = False

        if self._condition is not None:
            # Wake the monitor thread
            with self._condition:
                self._condition.notify()

        if self._thread is not None:
            if self._thread.isAlive():
                self._thread.join(timeout)

            if self._thread.isAlive():
                self._thread.terminate()

            self._thread = None

        self._delegate.shutdown(timeout)

    def _lifetime_monitor(self):

        while self._running:

            now = time.time()
            sleep_delta = None

            with self._lock:
                if self._last_render_time is not None:

                    idle_target = self.config['idle_shutdown_sec'] + self._last_render_time

                    if now >= idle_target:
                        self._logger.info(u"Shutting down idle renderer.")

                        self._last_render_time = None
                        self._start_time = None
                        self._delegate.shutdown()
                        self._running = False
                        break
                    else:
                        sleep_delta = idle_target - now

                if self._start_time is not None:

                    expired_target = self.config['max_lifetime_sec'] + self._start_time

                    if now >= expired_target:
                        self._logger.info(u"Shutting down renderer which reached max lifetime.")

                        self._last_render_time = None
                        self._start_time = None
                        self._delegate.shutdown()
                        self._running = False
                        break
                    else:
                        if sleep_delta is not None:
                            sleep_delta = min(sleep_delta, expired_target - now)
                        else:
                            sleep_delta = expired_target - now

            if sleep_delta is not None:
                with self._condition:
                    if self._running:
                        self._condition.wait(sleep_delta)