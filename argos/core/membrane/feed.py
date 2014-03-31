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

from argos.core.membrane import feedfinder, evaluator, extractor

import feedparser

from dateutil.parser import parse
from urllib import error

# For feedparser exceptions.
from xml.sax._exceptions import SAXException

from argos.util.logger import logger
logger = logger(__name__)

from http.client import BadStatusLine

def articles(source):
    """
    Parse a feed from the specified source,
    gathering the latest articles.

    The minimum length of an entry is
    500 characters. Anything under will be ignored.

    This will silently skip articles for which the full text
    can't be retrieved (i.e. if it returns 404).

    Some feeds, for whatever reason, do not include a `published`
    date in their entry data. In which case, it is left as an
    empty string.

    This does NOT return Article objects because it is quite expensive
    to create them.

    Instead this just passes out dictionaries
    where the keys are the kwarg names for Article
    initialization.

    Then argos.core.membrane.collector.collect
    can determine if a new Article should be created,
    and handle things accordingly.

    Args:
        | source (Source)    -- the source to fetch from.

    Returns:
        | list -- list of processed latest articles (as dicts).
    """
    # Fetch the feed data.
    data = feedparser.parse(source.ext_url)

    # If the `bozo` value is anything
    # but 0, there was an error parsing (or connecting) to the feed.
    if data.bozo:
        # Some errors are ok.
        if not isinstance(data.bozo_exception, feedparser.CharacterEncodingOverride) and not isinstance(data.bozo_exception, feedparser.NonXMLContentType):
            raise data.bozo_exception

    # Build the entry dicts.
    articles = []
    for entry in data.entries:

        # URL for this entry.
        url = entry['links'][0]['href']

        # Complete HTML content for this entry.
        try:
            entry_data, html = extractor.extract_entry_data(url)
        except (error.HTTPError, error.URLError, ConnectionResetError, BadStatusLine) as e:
            if type(e) == error.URLError or e.code == 404:
                # Can't reach, skip.
                logger.exception('Error extracting data for url {0}'.format(url))
                continue
            else:
                # Just skip so things don't break!
                logger.exception('Error extracting data for url {0}'.format(url))
                continue

        full_text = entry_data.cleaned_text

        # Skip over entries that are too short.
        if len(full_text) < 400:
            continue

        url = entry_data.canonical_link or url
        published = parse(entry.get('published')) if entry.get('published') else entry_data.publish_date
        updated = parse(entry.get('updated')) if entry.get('updated') else published
        title = entry.get('title', entry_data.title)

        # Download and save the top article image.
        image_url = extractor.extract_image(entry_data, filename=hash(url))

        articles.append({
            'ext_url':url,
            'source':source,
            'html':html,
            'text':full_text,
            'authors':extractor.extract_authors(entry),
            'tags':extractor.extract_tags(entry, known_tags=entry_data.tags),
            'title':title,
            'created_at':published,
            'updated_at':updated,
            'image':image_url,
            'score':evaluator.score(url)
            })

    return articles


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
