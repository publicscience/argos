#!../shallowthought-env/bin/python

import unittest
from membrane.feed import Feed
import membrane.feedfinder as feedfinder

class FeedTest(unittest.TestCase):
    def setUp(self):
        self.f = Feed()

    def tearDown(self):
        self.f = None

    def test_instance(self):
        self.assertIsInstance(self.f, Feed)


class FeedFinderTest(unittest.TestCase):
    def setUp(self):
        pass

    def tearDown(self):
        pass

    def test_feeds(self):
        feed_url = feedfinder.feeds('http://spaceandtim.es')
        self.assertEqual(feed_url, ['http://spaceandtim.es/feed'])

    def test_is_feed(self):
        self.assertTrue(feedfinder._is_feed('http://spaceandtim.es/feed/'))
