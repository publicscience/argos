#!../shallowthought-env/bin/python

import unittest
from membrane.feed import Feed

class FeedTest(unittest.TestCase):
    def setUp(self):
        self.f = Feed()

    def tearDown(self):
        self.f = None

    def test_instance(self):
        self.assertIsInstance(self.f, Feed)

    def test_get_feed(self):
        feed_url = self.f.get_feed('http://www.polygon.com/')
        self.assertEqual(feed_url, 'http://www.polygon.com/rss/index.xml')
