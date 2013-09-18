import unittest
import membrane.feed as feed
import membrane.feedfinder as feedfinder

class FeedTest(unittest.TestCase):
    def setUp(self):
        pass

    def tearDown(self):
        pass


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
