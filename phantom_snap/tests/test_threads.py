# coding=utf-8

from phantom_snap.threadtools import timed_method
import time
import traceback

class Timer:
    def __enter__(self):
        self.start = time.time()
        return self

    def __exit__(self, *args):
        self.end = time.time()
        self.interval = self.end - self.start

def loadTest():

    @timed_method(1, process=False)
    def func():
        return "Hi"

    total = 0.0

    for i in range(0, 100):
        with Timer() as t:
            print func()

        total += t.interval
        print ("After: %.3f" % t.interval)

    print ("Average: %.6f" % (total/i))

if __name__ == '__main__':

    import logging
    import sys
    logging.basicConfig(stream=sys.stdout, level=logging.INFO)

    loadTest()