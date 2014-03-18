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
from argos.core.models import Article

import feedparser

from dateutil.parser import parse
from urllib import error

# For feedparser exceptions.
from xml.sax._exceptions import SAXException

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
            full_text = entry_data.cleaned_text
        except (error.HTTPError, error.URLError) as e:
            if type(e) == error.URLError or e.code == 404:
                continue
            else:
                raise


        # Skip over entries that are too short.
        if len(full_text) < 400:
            continue

        url = entry_data.canonical_link or url
        published = parse(entry.get('published')) or entry_data.publish_date
        updated = parse(entry.get('updated')) or published
        title = entry.get('title', entry_data.title)

        # Download and save the top article image.
        image_url = extractor.extract_image(entry_data, filename=hash(url))

        articles.append(Article(
            ext_url=url,
            source=source,
            html=html,
            text=full_text,
            authors=extractor.extract_authors(entry),
            tags=extractor.extract_tags(entry, known_tags=entry_data.tags),
            title=title,
            created_at=published,
            updated_at=updated,
            image=image_url,
            score=evaluator.score(url)
       ))

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
