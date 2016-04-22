#!/usr/bin/env python

import ctypes
import inspect
import threading
import time
import traceback


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


class TimedMethod(object):
    """Provides a mechanism to use a timeout on a blocking function call."""

    def __init__(self):
        self._semaphore = threading.Semaphore()
        self._condition = threading.Condition(threading.RLock())

    def call(self, timeout, method, args=None, kwargs=None, join=False):

        self._semaphore.acquire()

        result = [None]
        t = Thread(target=self._threaded_method, args=(method, args, kwargs, result))
        t.setDaemon(True)
        t.start()

        with self._condition:
            current_time = start_time = time.time()

            while current_time < start_time + timeout:
                if self._semaphore.acquire(False):
                    return result[0]
                else:
                    self._condition.wait(timeout - current_time + start_time)
                    current_time = time.time()

        if t.isAlive():
            t.terminate()
            if join:
                t.join()

        return None

    def _threaded_method(self, method, args, kwargs, result):
        try:
            if args is None:
                if kwargs is None:
                    result[0] = method()
                else:
                    result[0] = method(**kwargs)
            else:
                if kwargs is None:
                    result[0] = method(*args)
                else:
                    result[0] = method(*args, **kwargs)
        except SystemExit:  # triggered by calling thread.terminate()
            raise
        except:  # exceptions that are unexpected
            traceback.print_exc()
        finally:
            self._semaphore.release()
            with self._condition:
                self._condition.notify()


# This Thread class comes from http://tomerfiliba.com/recipes/Thread2/
class Thread(threading.Thread):
    """ Extension of threading.Thread which provides the ability to terminate the thread."""

    def _get_my_tid(self):
        """determines this (self's) thread id"""
        if not self.isAlive():
            raise threading.ThreadError(u'The thread is not active')

        # do we have it cached?
        if hasattr(self, '_thread_id'):
            return self._thread_id

        # no, look for it in the _active dict
        for tid, tobj in threading._active.items():
            if tobj is self:
                self._thread_id = tid
                return tid

        raise AssertionError(u"Could not determine the thread's id")

    def raise_exc(self, exctype):
        """raises the given exception type in the context of this thread"""
        if not inspect.isclass(exctype):
            raise TypeError(u'Only types can be raised (not instances)')

        res = ctypes.pythonapi.PyThreadState_SetAsyncExc(ctypes.c_long(self._get_my_tid()), ctypes.py_object(exctype))

        if res == 0:
            raise ValueError(u'Invalid thread id')
        elif res != 1:
            # """if it returns a number greater than one, you're in trouble,
            # and you should call it again with exc=NULL to revert the effect"""
            ctypes.pythonapi.PyThreadState_SetAsyncExc(self._get_my_tid(), 0)
            raise SystemError(u'PyThreadState_SetAsyncExc failed')

    def terminate(self):
        """raises SystemExit in the context of the given thread, which should
        cause the thread to exit silently (unless caught)"""
        self.raise_exc(SystemExit)
