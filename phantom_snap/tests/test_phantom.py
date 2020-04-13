# coding=utf-8
import random
import string

from unittest import TestCase

from phantom_snap.settings import PHANTOMJS
from phantom_snap.phantom import PhantomJSRenderer
from phantom_snap.decorators import Lifetime

from phantom_snap.imagetools import save_image


class TestPhantomJS(TestCase):

    pass


if __name__ == '__main__':

    import logging
    import sys
    logging.basicConfig(stream=sys.stdout, level=logging.INFO)

    config = {
        'executable': '/usr/local/bin/phantomjs',
        'args': PHANTOMJS['args'] + ['--disk-cache=false', '--load-images=true'],
        'env': {'TZ': 'America/Los_Angeles'},
        'timeouts': {
            'process_startup': 100
        },
        'idle_shutdown_sec': 10,
        'max_lifetime_sec': 5
    }

    r = PhantomJSRenderer(config)
    r = Lifetime(r)

    with open('/tmp/crawl.html', 'r', encoding='utf-8', errors='replace') as content_file:
        html = content_file.read()

    urls = [('http://www.some-domain.com', html)]

    try:
        for url in urls:
            html = None
            if isinstance(url, tuple):
                html = url[1]
                url = url[0]

            print("Requesting {}".format(url))
            page = r.render(url=url, html=html, img_format='PNG')
            save_image('/tmp/render', page)

            import json
            if page and 'base64' in page:
                del page['base64']

            print(json.dumps(page, indent=4))

            if page is not None:
                if page['error'] is None:
                    print(''.join([page['url'], ' ', str(page['status']), ' ', str(page['load_time'])]))
                else:
                    print(''.join([page['url'], ' ', str(page['status']), ' ', page['error']]))
    finally:
        r.shutdown(10)