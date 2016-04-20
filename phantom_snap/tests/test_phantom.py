from unittest import TestCase

from phantom_snap.settings import PHANTOMJS
from phantom_snap.phantom import PhantomJSRenderer


class TestPhantomJS(TestCase):

    def test_is_string(self):

        pass


if __name__ == '__main__':

        config = {
            'executable': 'phantomjs',
            'args': PHANTOMJS['args'] + ['--disk-cache=false', '--load-images=true'],
            'env': {'TZ': 'America/Los_Angeles'}
        }
        r = PhantomJSRenderer(config)

        urls = ['http://whatismytimezone.com/',
                'http://www.drudgereport.com',
                'http://www.google.com']

        try:
            for url in urls:
                page = r.render(url)

                if page is not None:
                    if page['error'] is None:
                        print ''.join([page['url'], ' ', str(page['status']), ' ', str(page['load_time'])])
                    else:
                        print ''.join([page['url'], ' ', str(page['status']), ' ', page['error']])
        finally:
            r.shutdown(15)