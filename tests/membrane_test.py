from tests import RequiresMocks, RequiresApp
from models import Source, Article
from datetime import datetime
import membrane.feed as feed
import membrane.feedfinder as feedfinder
import membrane.collector as collector

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


class FeedTest(RequiresApp):
    def setUp(self):
        from unittest.mock import MagicMock
        self.setup_app()
        article = {
                'links': [{'href': 'some url'}],
                'title': 'some title',
                'published': 'some published date',
                'updated': 'some updated date'
        }
        data = MagicMock(
                    entries=[article],
                    bozo=False
               )
        self.mock_parse = self.create_patch('feedparser.parse', return_value=data)

        self.source = MagicMock()
        self.source.url = 'foo'

    def tearDown(self):
        self.teardown_app()

    def test_feed_error_if_no_full_text(self):
        self.assertRaises(Exception, feed.articles, self.source)

    def test_extract_tags(self):
        article = {
            'tags': [
                {'label': None,
                 'scheme': 'http://www.foreignpolicy.com/category/topic/military',
                 'term': 'Military'},
                {'label': None,
                 'scheme': 'http://www.foreignpolicy.com/category/topic/national_security',
                 'term': 'National Security'}
            ]
        }

        tags = feed.extract_tags(article)
        self.assertEqual(tags, ['Military', 'National Security'])

    def test_articles(self):
        self.create_patch('membrane.feed.fetch_full_text', return_value='''
            We have an infinite amount to learn both from nature and from each other
            The path of a cosmonaut is not an easy, triumphant march to glory. You have to get to know the meaning not just of joy but also of grief, before being allowed in the spacecraft cabin.
            Curious that we spend more time congratulating people who have succeeded than encouraging people who have not.
            There can be no thought of finishing for ‘aiming for the stars.’ Both figuratively and literally, it is a task to occupy the generations. And no matter how much progress one makes, there is always the thrill of just beginning.
            We want to explore. We’re curious people. Look back over history, people have put their lives at stake to go out and explore … We believe in what we’re doing. Now it’s time to go.
            Here men from the planet Earth first set foot upon the Moon. July 1969 AD. We came in peace for all mankind.
            There can be no thought of finishing for ‘aiming for the stars.’ Both figuratively and literally, it is a task to occupy the generations. And no matter how much progress one makes, there is always the thrill of just beginning.
            Where ignorance lurks, so too do the frontiers of discovery and imagination.
            Problems look mighty small from 150 miles up.
            I don't know what you could say about a day in which you have seen four beautiful sunsets.
            As we got further and further away, it [the Earth] diminished in size. Finally it shrank to the size of a marble, the most beautiful you can imagine. That beautiful, warm, living object looked so fragile, so delicate, that if you touched it with a finger it would crumble and fall apart. Seeing this has to change a man.
            Spaceflights cannot be stopped. This is not the work of any one man or even a group of men. It is a historical process which mankind is carrying out in accordance with the natural laws of human development.
            Space, the final frontier. These are the voyages of the Starship Enterprise. Its five-year mission: to explore strange new worlds, to seek out new life and new civilizations, to boldly go where no man has gone before.
            NASA is not about the ‘Adventure of Human Space Exploration’…We won’t be doing it just to get out there in space – we’ll be doing it because the things we learn out there will be making life better for a lot of people who won’t be able to go.
            I don't know what you could say about a day in which you have seen four beautiful sunsets.
        ''')
        articles = feed.articles(self.source)
        self.assertEquals(len(articles), 1)

    def test_articles_skips_short_articles(self):
        self.create_patch('membrane.feed.fetch_full_text', return_value='some full text')
        articles = feed.articles(self.source)
        self.assertEquals(len(articles), 0)

    def test_articles_skips_404_articles(self):
        from urllib import error
        self.create_patch('membrane.feed.fetch_full_text', side_effect=error.HTTPError(url=None, code=404, msg=None, hdrs=None, fp=None))
        articles = feed.articles(self.source)
        self.assertEquals(len(articles), 0)

    def test_articles_skips_unreachable_articles(self):
        from urllib import error
        self.create_patch('membrane.feed.fetch_full_text', side_effect=error.URLError('unreachable'))
        articles = feed.articles(self.source)
        self.assertEquals(len(articles), 0)

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


class CollectorTest(RequiresApp):
    def setUp(self):
        self.setup_app()

        # Add a fake source to work with.
        self.source = Source('foo')
        self.db.session.add(self.source)
        self.db.session.commit()

        # Mock articles.
        self.mock_articles = self.create_patch('membrane.feed.articles')

        # Mock finding feeds.
        self.mock_find_feed = self.create_patch('membrane.feed.find_feed')

    def tearDown(self):
        self.teardown_app()

    def test_collect(self):
        self.mock_articles.return_value = [
            Article(
                title='Foo',
                published=datetime.utcnow(),
                url='foo.com'
            )
        ]

        self.assertEquals(Article.query.count(), 0)

        collector.collect()

        self.assertEquals(Article.query.count(), 1)

        article = Article.query.first()
        self.assertEquals(article.title, 'Foo')

    def test_collect_ignores_existing(self):
        self.mock_articles.return_value = [
            Article(
                title='Foo',
                published=datetime.utcnow(),
                url='foo.com'
            )
        ]

        collector.collect()
        collector.collect()

        self.assertEquals(Article.query.count(), 1)

    def test_collect_error(self):
        self.assertEquals(self.source.errors, 0)

        self.mock_articles.side_effect = feed.SAXException('', None)

        collector.collect()

        self.assertEquals(self.source.errors, 1)

    def test_add_source(self):
        url = 'sup'
        self.mock_find_feed.return_value = url

        # 2 because the default test source has been added.
        collector.add_source(url)
        self.assertEquals(Source.query.count(), 2)

        # Ensure duplicates aren't added.
        collector.add_source(url)
        self.assertEquals(Source.query.count(), 2)

