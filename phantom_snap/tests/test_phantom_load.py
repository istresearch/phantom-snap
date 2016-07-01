# coding=utf-8

from unittest import TestCase

from phantom_snap.settings import PHANTOMJS
from phantom_snap.phantom import PhantomJSRenderer

import json, time, base64
import fileinput


class TestPhantomJS(TestCase):

    def test_is_string(self):

        pass


if __name__ == '__main__':

    import logging
    import sys
    logging.basicConfig(stream=sys.stdout, level=logging.INFO)

    config = {
        u'executable': '/usr/local/bin/phantomjs',
        u'args': PHANTOMJS['args'] + ['--disk-cache=false',
                                      '--load-images=true',
                                      '--ignore-ssl-errors=true',
                                      '--ssl-protocol=any'],
        u'env': {'TZ': 'America/Los_Angeles'},
        u'timeouts': {
            u'initial_render_response': 10,
            u'page_load': 3,
            u'render_response': 5,
            u'process_startup': 15
        }
    }
    r = PhantomJSRenderer(config)

    user_agent = 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_11_3) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/50.0.2661.102 Safari/537.36'

    errors = 0
    success = 0
    stop = 0
    fail = 0
    total = 0
    total_time = 0

    class Timer:
        def __enter__(self):
            self.start = time.time()
            return self

        def __exit__(self, *args):
            self.end = time.time()
            self.interval = self.end - self.start

    for line in fileinput.input(['/Users/andrew.carter/data/temp/pipe.elasticsearch.json.25000']):
        document = json.loads(line)

        if 'crawl' != document.get('type', ''):
            continue

        html = base64.decodestring(document.get('doc', {}).get('body', ''))
        url = document.get('doc', {}).get('url', '')
        result = None

        total += 1
        with Timer() as t:
            result = r.render(url, html=html, user_agent=user_agent)

        total_time += t.interval

        if result is not None:
            if result['error'] is None:
                if result['status'] == 'stopped':
                    stop += 1
                elif result['status'] == 'success':
                    success += 1
                else:
                    fail += 1

                print ''.join([document.get('uid'), ' ', str(result['status']), ' ', str(int(t.interval*1000)), ' ', str(result['load_time']), ' ', str(result['paint_time']), ' ', result['url']])
            else:
                errors += 1
                print ''.join([document.get('uid'), ' ', str(result['status']), ' ', str(int(t.interval*1000)), ' ', result['error'], ' ', result['url']])

        if total % 100 == 0:
            print "Total: {}\nSuccess: {}\nStop: {}\nFail: {}\nError: {}\nAverage time for hits: {}".format(total, success, stop, fail, errors, str(total_time / total))

        if total >= 10:
            pass#break

    r.shutdown(15)
    print "Total: {}\nSuccess: {}\nStop: {}\nFail: {}\nError: {}\nAverage time for hits: {}".format(total, success, stop, fail, errors, str(total_time / total))
