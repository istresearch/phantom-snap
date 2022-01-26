# coding=utf-8
from unittest import TestCase
from phantom_snap.cortex_renderer import CortexRenderer


class TestDocker(TestCase):
    import logging
    import sys
    logging.basicConfig(stream=sys.stdout, level=logging.INFO)

    def test_render_url(self):
        config = {
            'url': 'http://localhost:8080'
        }
        cortex_renderer = CortexRenderer(config)
        url = 'https://example.com/'
        # first 8 characters + last 8 characters or url website render
        truncated_base64 = 'iVBORw0K<truncated>TkSuQmCC'
        html = None

        print("Requesting {}".format(url))

        import json
        page = json.loads(cortex_renderer.render(url=url, html=html)['body'])

        if page and 'base64' in page:
            page['base64'] = page['base64'][0:8] + '<truncated>' + page['base64'][-8:]

        if page is not None:
            if page['error'] is None:
                print(''.join([page['url'], ' ', str(page['status']), ' ', str(page['load_time'])]))
            else:
                print(''.join([page['url'], ' ', str(page['status']), ' ', page['error']]))

        self.assertEqual(truncated_base64, page['base64'][0:8] + '<truncated>' + page['base64'][-8:])

    def test_render_html(self):
        config = {
            'url': 'http://localhost:8080'
        }
        cortex_renderer = CortexRenderer(config)
        url = 'https://example.com/'
        # first 8 characters + last 8 characters or html website render
        truncated_base64 = 'iVBORw0K<truncated>rkJggg=='
        html = '<html><body>Boo ya!</body></html>'

        print("Requesting {}".format(url))

        import json
        page = json.loads(cortex_renderer.render(url=url, html=html)['body'])

        if page and 'base64' in page:
            page['base64'] = page['base64'][0:8] + '<truncated>' + page['base64'][-8:]

        if page is not None:
            if page['error'] is None:
                print(''.join([page['url'], ' ', str(page['status']), ' ', str(page['load_time'])]))
            else:
                print(''.join([page['url'], ' ', str(page['status']), ' ', page['error']]))

        self.assertEqual(truncated_base64, page['base64'][0:8] + '<truncated>' + page['base64'][-8:])
