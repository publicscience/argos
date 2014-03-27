"""
Collector
==============

A corpus builder, for the sake of collecting
articles for training and/or testing.
"""

from argos.datastore import db
from argos.core.models import Source, Article, Event, Story
from argos.core.membrane import feed
from argos.util.logger import logger

from datetime import datetime, timedelta

# Logging.
logger = logger(__name__)

def collect():
    """
    Fetch articles from the sources,
    and save (or update) to db.

    This only creates, saves, and returns
    new Articles.
    """
    results = []

    logger.info('Fetching articles...')

    # Fetch entries for each source
    for source in Source.query.all():
        try:
            logger.info('Fetching from {0}...'.format(source.ext_url))
            raw_articles = feed.articles(source)

            # Check for existing copy.
            for raw_article in raw_articles:
                if not Article.query.filter_by(ext_url=raw_article['ext_url']).count():
                    article = Article(**raw_article)
                    db.session.add(article)
                    results.append(article)

        except feed.SAXException as e:
            # Error with the feed, make a note.
            logger.info('Error fetching from {0}.'.format(source.ext_url))
            source.errors += 1

    logger.info('Finished fetching articles.')

    db.session.commit()

    return results


def ponder():
    """
    This is a simple job
    which is meant to be run regularly.

    It collects the latest articles from
    all the sources and clusters them into events,
    and also clusters events from a recent timeframe
    into stories.
    """
    logger.info('Pondering...')
    articles = collect()
    Event.cluster(articles, threshold=0.05)

    # Cluster events from the past two weeks.
    # (two weeks is an arbitrary number, will need to choose a time frame)
    recent_events = Event.query.filter(Event.updated_at > datetime.utcnow() - timedelta(days=14)).all()
    Story.cluster(recent_events, threshold=0.05)


def add_source(url):
    """
    Add a new source.

    Args:
        | url (str)     -- where to look for the feed,
                           or the feed itself.
    """
    feed_url = feed.find_feed(url)
    if not Source.query.filter_by(ext_url=feed_url).count():
        source = Source(ext_url=feed_url)
        db.session.add(source)
        db.session.commit()


def add_sources(urls):
    """
    Add multiple sources.

    Args:
        | urls (list)   -- list of urls to look for feeds, or
                           the feed urls themselves.
    """
    for url in urls:
        feed_url = feed.find_feed(url)
        source = Source(ext_url=feed_url)
        db.session.add(source)
    db.session.commit()


def remove_source(url, delete_articles=False):
    """
    Remove a source.

    Args:
        | url (str)                 -- where to look for the feed,
                                       or the feed itself.
        | delete_articles (bool)    -- whether or not to delete articles
                                       from this source.
    """
    feed_url = feed.find_feed(url)
    source = Source.query.filter_by(ext_url=feed_url).first()

    if source:
        # If specified, delete articles associated with
        # this source.
        if delete_articles:
            for article in source.articles:
                db.session.delete(article)

        db.session.delete(source)

        db.session.commit()


def collect_sources(url):
    """
    Collects feed sources from the specified url,
    and adds them.

    Args:
        | url (str)     -- where to look for feeds.
    """
    feeds = feed.find_feeds(url)
    add_sources([f for f in feeds])


def load_sources_from_file(filepath='manage/sources.txt'):
    """
    Load feeds from a text file.
    Each line should be the url to the source
    you want to add.
    """
    logger.info('Loading sources from file. This may take awhile...')
    add_sources([line for line in open(filepath, 'r')])
