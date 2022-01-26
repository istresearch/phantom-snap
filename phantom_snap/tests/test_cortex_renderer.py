from unittest import TestCase
from phantom_snap.cortex_renderer import CortexRenderer
from mock import patch
from requests.exceptions import ConnectionError
import copy


class TestCortex(TestCase):

    def test_is_base64(self):
        cr = CortexRenderer({'url': 'my-url'})
        bad = '087124^7^*(*!$##bkasubasdzzz``'
        self.assertFalse(cr.is_base64(bad))

        bad2 = '<html><body>Boo ya!</body></html>'
        self.assertFalse(cr.is_base64(bad2))

        good = 'eW8gd2hhdCdzIHVwPw=='

        self.assertTrue(cr.is_base64(good))

    def test_prep_json(self):
        cr = CortexRenderer({'url': 'my-url'})

        # test no additional params
        expected = {
            'url': 'myurl',
            'img_format': 'png',
            'width': 5,
            'height': 6,
            'html_encoding': 'utf-8',
        }
        self.assertEqual(cr._prep_json(url='myurl',
                                       html=None,
                                       img_format='png',
                                       width=5,
                                       height=6,
                                       page_load_timeout=None,
                                       user_agent=None,
                                       headers=None,
                                       cookies=None,
                                       html_encoding=u'utf-8',
                                       http_proxy=None), expected)

        # test all additional params, not encoded html
        expected = {
            'url': 'myurl',
            'img_format': 'png',
            'width': 5,
            'height': 6,
            'html_encoding': 'utf-8',
            'html': 'PGRpdj5oZXk8L2Rpdj4=',
            'page_load_timeout': 8,
            'user_agent': 'Mozilla',
            'headers': {'key': 'value'},
            'cookies': {'value': 'key'},
        }
        self.assertEqual(cr._prep_json(url='myurl',
                                       html='<div>hey</div>',
                                       img_format='png',
                                       width=5,
                                       height=6,
                                       page_load_timeout=8,
                                       user_agent='Mozilla',
                                       headers={'key': 'value'},
                                       cookies={'value': 'key'},
                                       html_encoding=u'utf-8',
                                       http_proxy=None), expected)

        # test all additional params, encoded html
        expected = {
            'url': 'myurl',
            'img_format': 'png',
            'width': 5,
            'height': 6,
            'html_encoding': 'utf-8',
            'html': 'PGRpdj5oZXk8L2Rpdj4=',
            'page_load_timeout': 8,
            'user_agent': 'Mozilla',
            'headers': {'key': 'value'},
            'cookies': {'value': 'key'},
        }
        self.assertEqual(cr._prep_json(url='myurl',
                                       html='PGRpdj5oZXk8L2Rpdj4=',
                                       img_format='png',
                                       width=5,
                                       height=6,
                                       page_load_timeout=8,
                                       user_agent='Mozilla',
                                       headers={'key': 'value'},
                                       cookies={'value': 'key'},
                                       html_encoding=u'utf-8',
                                       http_proxy=None), expected)

    def test_prep_headers(self):
        # default
        cr = CortexRenderer({'url': 'my-url'})
        expected = {
            'content-type': 'application/json'
        }
        self.assertEqual(cr._prep_headers(), expected)

        # with config
        cr = CortexRenderer({'url': 'my-url', 'api_key': 'secret'})
        expected = {
            'content-type': 'application/json',
            'x-api-key': 'secret'
        }
        self.assertEqual(cr._prep_headers(), expected)

    def test_prep_timeout(self):
        # default
        cr = CortexRenderer({'url': 'my-url'})
        expected = 120
        self.assertEqual(cr._prep_timeout(), expected)

        # with config
        cr = CortexRenderer({'url': 'my-url', 'timeouts': {'request_timeout': 20}})
        expected = 20
        self.assertEqual(cr._prep_timeout(), expected)

    def test_render(self):
        lr = CortexRenderer({'url': 'my-url'})

        # Mock Request Response Object
        class ReqRes(object):
            def __init__(self, o, s):
                self.o = o
                self.status_code = s

            def json(self):
                return self.o

        with patch('requests.post') as r:
            # perfect result
            res = {
                u'status': u'success',
                u'format': u'PNG',
                u'url': u'http://www.urlhere.com',
                u'paint_time': 212,
                u'base64': u'iVBORw0KGgoA...<truncated>...CYII=',
                u'error': None,
                u'load_time': 4
            }
            r.return_value = ReqRes(res, 200)
            self.assertEqual(lr.render({'url': 'http://www.urlhere.com'}),
                             res)

            # requests execption
            with patch('traceback.format_exc') as t:
                t.return_value = 'this is bad'
                r.side_effect = ConnectionError('bad')
                res = {
                    u'status': u'fail',
                    u'format': u'PNG',
                    u'url': 'http://www.urlhere.com',
                    u'paint_time': None,
                    u'base64': None,
                    u'error': 'this is bad',
                    u'load_time': None,
                }
                self.assertEqual(lr.render(url='http://www.urlhere.com'),
                                 res)

            # bad json
            with patch('traceback.format_exc') as t:
                t.return_value = 'this is bad again'
                r.side_effect = ValueError('bad again')
                res = {
                    u'status': u'fail',
                    u'format': u'PNG',
                    u'url': 'http://www.urlhere.com',
                    u'paint_time': None,
                    u'base64': None,
                    u'error': 'this is bad again',
                    u'load_time': None,
                }
                self.assertEqual(lr.render(url='http://www.urlhere.com'),
                                 res)

            # invalid status code
            r.side_effect = None
            res = {
                u'status': u'fail',
                u'format': u'PNG',
                u'url': u'http://www.urlhere.com',
                u'paint_time': None,
                u'base64': None,
                u'error': None,
                u'load_time': None,
            }
            res_copy = copy.deepcopy(res)
            res_copy['message'] = "Internal Error"
            res_copy['ex'] = "traceback_here"
            r.return_value = ReqRes(res_copy, 500)
            res['error'] = "traceback_here"
            self.assertEqual(lr.render(url='http://www.urlhere.com'),
                             res)


