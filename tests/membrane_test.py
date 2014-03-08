from tests import RequiresMocks, RequiresApp
import tests.factories as fac
from unittest.mock import MagicMock
from datetime import datetime

import argos.core.membrane.feed as feed
import argos.core.membrane.feedfinder as feedfinder
import argos.core.membrane.collector as collector
import argos.core.membrane.evaluator as evaluator

from argos.core.models import Source, Article, Author

from io import BytesIO
import os

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

full_text = """
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
"""

html_doc = open('tests/data/article.html', 'r').read()


class FeedTest(RequiresApp):
    patch_knowledge = True
    patch_entities = True

    def setUp(self):
        article = {
                'links': [{'href': 'some url'}],
                'title': 'some title',
                'published': 'Thu, 09 Jan 2014 14:00:00 GMT',
                'updated': 'Thu, 09 Jan 2014 14:00:00 GMT'
        }
        data = MagicMock(
                    entries=[article],
                    bozo=False
               )
        self.mock_parse = self.create_patch('feedparser.parse', return_value=data)

        self.source = Source(ext_url='foo')

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

        tags = feed.extract_tags(article, known_tags=set(['Helicopters']))
        self.assertEqual(set(tags), set(['Military', 'National Security', 'Helicopters']))

    def test_extract_single_authors(self):
        articles = [{
                'author': 'John Heimer'
            },{
                'author_detail': {
                    'name': 'John Heimer'
                }
            }, {
                'author_detail': {
                    'name': 'By John Heimer'
                }
            }, {
                'author_detail': {
                    'name': 'BY JOHN HEIMER'
                }
            }
        ]
        for article in articles:
            authors = feed.extract_authors(article)
            self.assertEqual(authors[0].name, 'John Heimer')
            self.assertEqual(Author.query.count(), 1)

    def test_extract_multiple_authors_and(self):
        article = {
            'author_detail': {
                'name': 'BY JOHN HEIMER and BEN HUBBARD'
            }
        }
        authors = feed.extract_authors(article)
        author_names = [author.name for author in authors]
        self.assertEqual(author_names, ['John Heimer', 'Ben Hubbard'])
        self.assertEqual(Author.query.count(), 2)

    def test_extract_multiple_authors_comma(self):
        article = {
            'author_detail': {
                'name': 'BY JOHN HEIMER, HWAIDA SAAD, and BEN HUBBARD'
            }
        }
        authors = feed.extract_authors(article)
        author_names = [author.name for author in authors]
        self.assertEqual(author_names, ['John Heimer', 'Hwaida Saad', 'Ben Hubbard'])
        self.assertEqual(Author.query.count(), 3)

    def test_extract_multiple_authors_no_oxford_comma(self):
        article = {
            'author_detail': {
                'name': 'BY JOHN HEIMER, HWAIDA SAAD and BEN HUBBARD'
            }
        }
        authors = feed.extract_authors(article)
        author_names = [author.name for author in authors]
        self.assertEqual(author_names, ['John Heimer', 'Hwaida Saad', 'Ben Hubbard'])
        self.assertEqual(Author.query.count(), 3)


    def test_articles(self):
        extracted_data = MagicMock()
        extracted_data.cleaned_text = full_text
        extracted_data.canonical_link = 'a canonical link'

        # Mock the download method to return some local image path.
        self.create_patch('argos.core.membrane.feed.download', return_value='/foo/bar/image.jpg')

        # Mock the evaluator score calculation.
        self.create_patch('argos.core.membrane.evaluator.score', return_value=100)

        self.create_patch('argos.core.membrane.feed.extract_entry_data', return_value=(extracted_data, full_text))
        articles = feed.articles(self.source)
        self.assertEquals(len(articles), 1)

    def test_articles_skips_short_articles(self):
        extracted_data = MagicMock()
        extracted_data.cleaned_text = 'short full text'
        self.create_patch('argos.core.membrane.feed.extract_entry_data', return_value=(extracted_data, 'short full text'))
        articles = feed.articles(self.source)
        self.assertEquals(len(articles), 0)

    def test_articles_skips_404_articles(self):
        from urllib import error
        self.create_patch('argos.core.membrane.feed.extract_entry_data', side_effect=error.HTTPError(url=None, code=404, msg=None, hdrs=None, fp=None))
        articles = feed.articles(self.source)
        self.assertEquals(len(articles), 0)

    def test_articles_skips_unreachable_articles(self):
        from urllib import error
        self.create_patch('argos.core.membrane.feed.extract_entry_data', side_effect=error.URLError('unreachable'))
        articles = feed.articles(self.source)
        self.assertEquals(len(articles), 0)

    def test_extract_entry_data(self):
        self.create_patch('argos.core.membrane.feed._get_html', return_value=html_doc)
        data, html = feed.extract_entry_data('http://foo.com')
        expected = {
                'title': 'Why Israel Fears the Boycott',
                'image': 'http://static01.nyt.com/images/2014/02/01/opinion/sunday/01goodman/01goodman-videoSixteenByNine1050.jpg'
        }
        results = {
                'title': data.title,
                'image': data.top_image.src
        }
        self.assertEqual(expected, results)

    def test_extract_image(self):
        entry_data = MagicMock()
        entry_data.top_image.src = 'http://foo.com/bar/image.jpg'
        expected_url = 'tests/data/downloaded.jpg'

        if os.path.isfile(expected_url):
            os.remove(expected_url)

        # Mock response for downloading.
        image_data = open('tests/data/image.jpg', 'rb').read()
        mock_response = BytesIO(image_data)
        mock_response.headers = {
            'Accept-Ranges': 'bytes',
            'Last-Modified': 'Wed, 05 Sep 2013 08:53:26 GMT',
            'Content-Length': str(len(image_data))
        }
        mock_urlopen = self.create_patch('urllib.request.urlopen', return_value=mock_response)

        image_url = feed.extract_image(entry_data, filename='downloaded.jpg', save_dir='tests/data/')

        self.assertEqual(image_url, expected_url)
        self.assertTrue(os.path.isfile(expected_url))
        self.assertEqual(len(image_data), len(open(expected_url, 'rb').read()))


class FeedFinderTest(RequiresMocks):
    def setUp(self):
        self.mock_get = self.create_patch('argos.core.membrane.feedfinder._get')

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
    patch_knowledge = True

    def setUp(self):
        # Add a fake source to work with.
        self.source = Source(ext_url='foo')
        self.db.session.add(self.source)
        self.db.session.commit()

        # Mock articles.
        self.mock_articles = self.create_patch('argos.core.membrane.feed.articles')

        # Mock finding feeds.
        self.mock_find_feed = self.create_patch('argos.core.membrane.feed.find_feed')

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


class EvaluatorTest(RequiresApp):
    url = 'test'

    def test_facebook(self):
        body = b"""
            <links_getStats_response xmlns="http://api.facebook.com/1.0/" xmlns:xsi="http://www.w3.org/2001/XMLSchema-instance" xsi:schemaLocation="http://api.facebook.com/1.0/ http://api.facebook.com/1.0/facebook.xsd" list="true">
                <link_stat>
                    <url>www.google.com</url>
                    <normalized_url>http://www.google.com/</normalized_url>
                    <share_count>5402940</share_count>
                    <like_count>1371562</like_count>
                    <comment_count>1728901</comment_count>
                    <total_count>8503403</total_count>
                    <click_count>265614</click_count>
                    <comments_fbid>381702034999</comments_fbid>
                    <commentsbox_count>841</commentsbox_count>
                </link_stat>
            </links_getStats_response>
        """
        mock_resp = MagicMock()
        mock_resp.status = 200
        mock_resp.read.return_value = body

        self.create_patch('urllib.request.urlopen', return_value=mock_resp)
        self.assertEqual(evaluator.facebook(self.url), 66403.5 + 8503403 + 841)

    def test_facebook_graph(self):
        body = b'{"id":"http:\\/\\/www.google.com","shares":8503603,"comments":841}'
        mock_resp = MagicMock()
        mock_resp.status = 200
        mock_resp.read.return_value = body

        self.create_patch('urllib.request.urlopen', return_value=mock_resp)
        self.assertEqual(evaluator.facebook_graph(self.url), 8503603 + 841)

    def test_twitter(self):
        body = b'{"count":19515036,"url":"http:\\/\\/www.google.com\\/"}'
        mock_resp = MagicMock()
        mock_resp.status = 200
        mock_resp.read.return_value = body

        self.create_patch('urllib.request.urlopen', return_value=mock_resp)
        self.assertEqual(evaluator.twitter(self.url), 19515036)

    def test_linkedin(self):
        body = b'{"count":63952,"fCnt":"63K","fCntPlusOne":"63K","url":"http:\\/\\/www.google.com"}'
        mock_resp = MagicMock()
        mock_resp.status = 200
        mock_resp.read.return_value = body

        self.create_patch('urllib.request.urlopen', return_value=mock_resp)
        self.assertEqual(evaluator.linkedin(self.url), 63952)

    def test_stumbleupon(self):
        body = b'{"result":{"url":"http:\\/\\/www.google.com\\/","in_index":true,"publicid":"2pI1xR","views":254956,"title":"Google","thumbnail":"http:\\/\\/cdn.stumble-upon.com\\/mthumb\\/31\\/10031.jpg","thumbnail_b":"http:\\/\\/cdn.stumble-upon.com\\/bthumb\\/31\\/10031.jpg","submit_link":"http:\\/\\/www.stumbleupon.com\\/submit\\/?url=http:\\/\\/www.google.com\\/","badge_link":"http:\\/\\/www.stumbleupon.com\\/badge\\/?url=http:\\/\\/www.google.com\\/","info_link":"http:\\/\\/www.stumbleupon.com\\/url\\/www.google.com\\/"},"timestamp":1393900890,"success":true}'
        mock_resp = MagicMock()
        mock_resp.status = 200
        mock_resp.read.return_value = body

        self.create_patch('urllib.request.urlopen', return_value=mock_resp)
        self.assertEqual(evaluator.stumbleupon(self.url), 254956)
