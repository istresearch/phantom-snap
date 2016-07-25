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

if __name__ == '__main__':

    import logging
    import sys
    logging.basicConfig(stream=sys.stdout, level=logging.INFO)

    @timed_method(1, process=True)
    def func(index):
        import time
        try:
            while True:
                time.sleep(0.2)
                print "slept " + str(index)
                break
        except:
            print "EXIT " + str(index) + ' ' + traceback.format_exc()
            raise

        return 'done with ' + str(index)

    for i in range(0, 10):
        with Timer() as t:
            r = func(i)
            if r is not None:
                print "got " + r
            else:
                print "got nothing"

        print ("After: %.3f" % t.interval)

    time.sleep(2)
