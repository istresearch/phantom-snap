# coding=utf-8
# These commented tests will cause circlci to fail unless there is a running phantom-snap image
# TODO create and push phantom-snap docker image to dockerhub repository and include in config.yml
#
# from unittest import TestCase
# from phantom_snap.cortex_renderer import CortexRenderer
#
#
# class TestDocker(TestCase):
#     import logging
#     import sys
#     logging.basicConfig(stream=sys.stdout, level=logging.INFO)
#
#     def test_render_url(self):
#         config = {
#             'url': 'http://localhost:8080'
#         }
#         cortex_renderer = CortexRenderer(config)
#         url = 'https://example.com/'
#         # first 8 characters + last 8 characters or url website render
#         truncated_base64 = 'iVBORw0K<truncated>TkSuQmCC'
#         html = None
#
#         print("Requesting {}".format(url))
#
#         import json
#         page = json.loads(cortex_renderer.render(url=url, html=html)['body'])
#
#         if page and 'base64' in page:
#             page['base64'] = page['base64'][0:8] + '<truncated>' + page['base64'][-8:]
#
#         if page is not None:
#             if page['error'] is None:
#                 print(''.join([page['url'], ' ', str(page['status']), ' ', str(page['load_time'])]))
#             else:
#                 print(''.join([page['url'], ' ', str(page['status']), ' ', page['error']]))
#
#         self.assertEqual(truncated_base64, page['base64'][0:8] + '<truncated>' + page['base64'][-8:])
#
#     def test_render_html(self):
#         config = {
#             'url': 'http://localhost:8080'
#         }
#         cortex_renderer = CortexRenderer(config)
#         url = 'https://example.com/'
#         # first 8 characters + last 8 characters or html website render
#         truncated_base64 = 'iVBORw0K<truncated>rkJggg=='
#         html = '<html><body>Boo ya!</body></html>'
#
#         print("Requesting {}".format(url))
#
#         import json
#         page = json.loads(cortex_renderer.render(url=url, html=html)['body'])
#
#         if page and 'base64' in page:
#             page['base64'] = page['base64'][0:8] + '<truncated>' + page['base64'][-8:]
#
#         if page is not None:
#             if page['error'] is None:
#                 print(''.join([page['url'], ' ', str(page['status']), ' ', str(page['load_time'])]))
#             else:
#                 print(''.join([page['url'], ' ', str(page['status']), ' ', page['error']]))
#
#         self.assertEqual(truncated_base64, page['base64'][0:8] + '<truncated>' + page['base64'][-8:])

#Manual tests
class DockerTest():
    import logging
    import sys
    logging.basicConfig(stream=sys.stdout, level=logging.INFO)

    def test_render_url(self):
        print('Attempting to render URL: TEST 1/2')
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

        if truncated_base64 == page['base64'][0:8] + '<truncated>' + page['base64'][-8:]:
            print('Rendering URL test succeeded')

    def test_render_html(self):
        print('Attempting to render HTML: TEST 2/2')
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

        if truncated_base64 == page['base64'][0:8] + '<truncated>' + page['base64'][-8:]:
            print('Rendering HTML test succeeded')



if __name__ == '__main__':
    import sys
    from pathlib import Path
    sys.path.append(str(Path(__file__).parent.parent.parent.absolute()))
    from phantom_snap.cortex_renderer import CortexRenderer
    ts = DockerTest()
    ts.test_render_url()
    ts.test_render_html()
