import unittest
from tests import RequiresMocks
import membrane.feed as feed
import membrane.feedfinder as feedfinder

# Some testing data.
mock_page = """
    <!doctype html>
        <head>
            <title>space & times</title>
        </head>
        <body></body>
    </html>
    """

mock_page_with_feed = """
    <!doctype html>
        <head>
            <title>space & times</title>
            <link rel="alternate" type="application/rss+xml" href="http://test.com/feed.xml">
        </head>
        <body></body>
    </html>
    """

mock_feed = """
    <?xml version="1.0" encoding="utf-8"?>
    <rss version="2.0"
        xmlns:content="http://purl.org/rss/1.0/modules/content/"
        xmlns:wfw="http://wellformedweb.org/commentapi/"
        xmlns:dc="http://purl.org/dc/elements/1.1/"
        xmlns:atom="http://www.w3.org/2005/atom"
        xmlns:sy="http://purl.org/rss/1.0/modules/syndication/"
        xmlns:slash="http://purl.org/rss/1.0/modules/slash/"
        >

        <channel>
            <title>space and times</title>
            <atom:link href="http://spaceandtim.es/feed/" rel="self" type="application/rss+xml" />
            <link>http://spaceandtim.es</link>
            <description>things</description>
            <item></item>
        </channel>
    </rss>
"""


class FeedTest(unittest.TestCase):
    def setUp(self):
        pass

    def tearDown(self):
        pass

    def test_feed_error(self):
        self.assertRaises(Exception, feed.entries, 'foo')


class FeedFinderTest(RequiresMocks):
    def setUp(self):
        self.mock_get = self.create_patch('membrane.feedfinder._get')

    def tearDown(self):
        pass

    def test_finds_feeds_if_already_feed(self):
        self.mock_get.return_value = mock_feed
        feed_url = feedfinder.feeds('http://test.com')
        self.assertEqual(feed_url, ['http://test.com'])

    def test_finds_wordpress_feeds(self):
        # Mock to look like a Wordpress feed.
        def side_effect(param):
            return mock_feed if param == 'http://test.com/feed' else mock_page

        self.mock_get.side_effect = side_effect
        feed_url = feedfinder.feeds('http://test.com')
        self.assertEqual(feed_url, ['http://test.com/feed'])

    def test_get_feed_links(self):
        feed_url = feedfinder._get_feed_links(mock_page_with_feed, 'http://test.com')
        self.assertEqual(feed_url, ['http://test.com/feed.xml'])

    def test_get_feed_links_without_links(self):
        feed_url = feedfinder._get_feed_links(mock_page, 'http://test.com')
        self.assertEqual(feed_url, [])

    def test_is_feed(self):
        self.mock_get.return_value = mock_feed
        self.assertTrue(feedfinder._is_feed('http://test.com/feed/'))

    def test_is_not_feed(self):
        self.mock_get.return_value = mock_page
        self.assertFalse(feedfinder._is_feed('http://test.com/'))

