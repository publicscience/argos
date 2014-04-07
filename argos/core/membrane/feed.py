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
from argos.core.models import Source, Feed
from argos.core.membrane import feedfinder

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


def add_sources(sources):
    """
    Add multiple sources.

    Args:
        | sources (list)   -- list of dicts of urls to look for feeds, or
                              the feed urls themselves, and the source name::

        {
            'The New York Times': [
                'http//www.nytimes.com/services/xml/rss/nyt/World.xml',
                'http//www.nytimes.com/services/xml/rss/nyt/politics.xml'
            ]
        }
    """
    for name, feeds in sources.items():

        # Get/create the Source.
        source = Source.query.filter_by(name=name).first()
        if not source:
            source = Source(name=name)
            db.session.add(source)

        # Add the feeds.
        for feed in feeds:
            feed_url = find_feed(feed)
            if not Feed.query.filter_by(ext_url=feed_url).count():
                feed = Feed(ext_url=feed_url, source=source)
                db.session.add(feed)

    db.session.commit()
