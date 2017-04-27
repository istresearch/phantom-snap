#!/usr/bin/env python

import time
from eventlet.green import threading


class TimedRLock(object):
    """A re-entrant lock that provides acquisition timeout."""

    def __init__(self):
        self._lock = threading.RLock()
        self._condition = threading.Condition(threading.RLock())

    def acquire(self, blocking=True, timeout=None):

        if timeout is not None:
            with self._condition:
                current_time = start_time = time.time()

                while current_time < start_time + timeout:
                    if self._lock.acquire(False):
                        return True
                    else:
                        self._condition.wait(timeout - current_time + start_time)
                        current_time = time.time()
            return False
        else:
            return self._lock.acquire(blocking)

    def release(self):
        self._lock.release()
        with self._condition:
            self._condition.notify()

    def __enter__(self):
        """Used by the 'with' statement"""
        self.acquire()

    def __exit__(self, type, value, traceback):
        """Used by the 'with' statement"""
        self.release()
