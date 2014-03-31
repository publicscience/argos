"""
Feed
==============

Provides an interface for
accessing RSS feeds.

Example::

    # Print articles from a feed.
    site = 'http://www.polygon.com/'
    feed_url = find_feed(site)
    source = Source(feed_url)
    print(articles(source))
"""

from argos.datastore import db
from argos.core.models import Source
from argos.core.membrane import feedfinder

import json

from argos.util.logger import logger
logger = logger(__name__)


def find_feed(url):
    """
    Find the RSS feed url for a site.
    Returns the first eligible feed.

    Args:
        | url (str)    -- the url of the site to search.

    Returns:
        | str -- the discovered feed url.
    """
    return feedfinder.feed(url)


def find_feeds(url):
    """
    Find the RSS feed urls for a site.
    Returns all eligible feeds.

    Args:
        | url (str)    -- the url of the site to search.

    Returns:
        | list -- a list of the feed urls.
    """
    return feedfinder.feeds(url)


def add_source(url, name):
    """
    Add a new source.

    Args:
        | url  (str)     -- where to look for the feed,
                            or the feed itself.
        | name (str)     -- the name for the source.
    """
    feed_url = find_feed(url)
    if not Source.query.filter_by(ext_url=feed_url).count():
        source = Source(ext_url=feed_url, name=name)
        db.session.add(source)
        db.session.commit()


def add_sources(sources):
    """
    Add multiple sources.

    Args:
        | sources (list)   -- list of dicts of urls to look for feeds, or
                              the feed urls themselves, and the source name::

        [{
            'name': 'The New York Times',
            'url': 'http//www.nytimes.com/services/xml/rss/nyt/World.xml'
        }]
    """
    for raw_source in sources:
        feed_url = find_feed(raw_source['url'])
        if not Source.query.filter_by(ext_url=feed_url).count():
            source = Source(ext_url=feed_url, name=raw_source['name'])
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
    feed_url = find_feed(url)
    source = Source.query.filter_by(ext_url=feed_url).first()

    if source:
        # If specified, delete articles associated with
        # this source.
        if delete_articles:
            for article in source.articles:
                db.session.delete(article)

        db.session.delete(source)

        db.session.commit()


def collect_sources(url, name):
    """
    Collects feed sources from the specified url,
    and adds them.

    Args:
        | url  (str)     -- where to look for feeds.
        | name (str)     -- the name of the source.
    """
    feeds = find_feeds(url)
    add_sources([{'name': name, 'url': f} for f in feeds])


def load_sources_from_file(filepath='manage/sources.json'):
    """
    Load feeds from a JSON file.
    It should consist of an array of arrays like so::

        [
            ["The Atlantic", "http://feeds.feedburner.com/AtlanticNational"],
            ["The New York Times", "http://www.nytimes.com/services/xml/rss/nyt/World.xml"]
        ]
    """
    logger.info('Loading sources from file. This may take awhile...')
    sources = open(filepath, 'r')
    raw_sources = json.load(sources)
    add_sources([{'name': src[0], 'url': src[1]} for src in raw_sources])
