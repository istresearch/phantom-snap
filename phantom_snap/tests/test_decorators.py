# coding=utf-8

import eventlet
import copy

from unittest import TestCase
from mock import MagicMock

from phantom_snap.settings import PHANTOMJS
from phantom_snap.renderer import Renderer
from phantom_snap.decorators import Lifetime


class MockRenderer(Renderer):

    def __init__(self, config):

        self.config = copy.deepcopy(PHANTOMJS)
        self.config.update(config)

    def get_config(self):
        return self.config

    def render(self, url, html=None, img_format='PNG', width=1280, height=1024, page_load_timeout=None, user_agent=None,
               headers=None, cookies=None, html_encoding=u'utf-8'):
        pass

    def shutdown(self, timeout=None):
        pass


class TestPhantomJS(TestCase):

    def test_lifetime(self):

        mock_r = MockRenderer({})
        mock_r.render = MagicMock(side_effect=['result'])
        mock_r.shutdown = MagicMock()

        r = Lifetime(mock_r)

        self.assertEqual(mock_r.render.call_count, 0)
        self.assertEqual(mock_r.shutdown.call_count, 0)

        self.assertEqual(r.render(u'http://test'), 'result')

        self.assertEqual(mock_r.render.call_count, 1)
        self.assertEqual(mock_r.shutdown.call_count, 0)
        r.shutdown()

        self.assertEqual(mock_r.render.call_count, 1)
        self.assertEqual(mock_r.shutdown.call_count, 1)

    def test_lifetime_idle(self):

        mock_r = MockRenderer({
            'idle_shutdown_sec': 0.5,
            'max_lifetime_sec': 60
        })

        mock_r.render = MagicMock()
        mock_r.shutdown = MagicMock()

        r = Lifetime(mock_r)

        self.assertEqual(mock_r.render.call_count, 0)
        self.assertEqual(mock_r.shutdown.call_count, 0)

        eventlet.sleep(0.25)
        r.render(u'http://test')

        self.assertEqual(mock_r.render.call_count, 1)
        self.assertEqual(mock_r.shutdown.call_count, 0)

        eventlet.sleep(.25)
        r.render(u'http://test')

        self.assertEqual(mock_r.render.call_count, 2)
        self.assertEqual(mock_r.shutdown.call_count, 0)

        eventlet.sleep(.25)
        r.render(u'http://test')

        self.assertEqual(mock_r.render.call_count, 3)
        self.assertEqual(mock_r.shutdown.call_count, 0)

        eventlet.sleep(.25)
        r.render(u'http://test')

        self.assertEqual(mock_r.render.call_count, 4)
        self.assertEqual(mock_r.shutdown.call_count, 0)

        eventlet.sleep(.75)

        self.assertEqual(mock_r.render.call_count, 4)
        self.assertEqual(mock_r.shutdown.call_count, 1)

        r.render(u'http://test')

        self.assertEqual(mock_r.render.call_count, 5)
        self.assertEqual(mock_r.shutdown.call_count, 1)

        r.shutdown()

        self.assertEqual(mock_r.render.call_count, 5)
        self.assertEqual(mock_r.shutdown.call_count, 2)

    def test_lifetime_max(self):

        mock_r = MockRenderer({
            'idle_shutdown_sec': 60,
            'max_lifetime_sec': 0.5
        })

        mock_r.render = MagicMock()
        mock_r.shutdown = MagicMock()

        r = Lifetime(mock_r)

        self.assertEqual(mock_r.render.call_count, 0)
        self.assertEqual(mock_r.shutdown.call_count, 0)

        eventlet.sleep(0.25)
        r.render(u'http://test')

        self.assertEqual(mock_r.render.call_count, 1)
        self.assertEqual(mock_r.shutdown.call_count, 0)

        eventlet.sleep(0.5)
        r.render(u'http://test')

        self.assertEqual(mock_r.render.call_count, 2)
        self.assertEqual(mock_r.shutdown.call_count, 1)

        eventlet.sleep(0.5)
        r.render(u'http://test')

        self.assertEqual(mock_r.render.call_count, 3)
        self.assertEqual(mock_r.shutdown.call_count, 2)

        r.shutdown()

        self.assertEqual(mock_r.render.call_count, 3)
        self.assertEqual(mock_r.shutdown.call_count, 3)