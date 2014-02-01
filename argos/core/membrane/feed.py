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

import feedparser
import time
from dateutil.parser import parse
from models import Article
from urllib import request, error
from http.client import IncompleteRead
from http.cookiejar import CookieJar
from . import feedfinder
from brain import trim, sanitize, entities
from readability.readability import Document

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
    data = feedparser.parse(source.url)

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
            html = fetch_full_text(url)
            entry['fulltext'] = trim(sanitize(html))
        except (error.HTTPError, error.URLError) as e:
            if type(e) == error.URLError or e.code == 404:
                continue
            else:
                raise


        # Skip over entries that are too short.
        if len(entry['fulltext']) < 400:
            continue

        articles.append(Article(
            url=url,
            source=source,
            html=html,
            text=entry['fulltext'],
            authors=[entry.get('author', None)], # NEED BETTER HANDLING OF THIS
            tags=extract_tags(entry),
            title=entry['title'],
            created_at=parse(entry.get('published', '')),
            updated_at=parse(entry.get('updated', entry.get('published', '')))
       ))

    return articles

def extract_tags(article):
    """
    Extract tags from a feed's article,
    returning it in a simpler format (a list of strings).

    Args:
        | article (Article)   -- the article

    This operates assuming the tags are formatted like so::

        [{'label': None,
             'scheme': 'http://www.foreignpolicy.com/category/topic/military',
             'term': 'Military'},
        {'label': None,
             'scheme': 'http://www.foreignpolicy.com/category/topic/national_security',
             'term': 'National Security'}]

    This seems to be the standard.

    But there is a fallback if these tags are not supplied.
    Named Entity Recognition is used as a rough approximation of tags.
    """
    # If tags are supplied, use them.
    if 'tags' in article:
        return [tag['term'] for tag in article['tags']]

    # DISABLING FOR NOW. Easier to run through all entries and add
    # these entities later.
    # Otherwise, try to extract some.
    #else:
        #sample = article['fulltext']
        #return entities(sample)

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


def fetch_full_text(url):
    """
    Fetch the full content for a feed entry url.

    Args:
        | url (str)    -- the url of the entry.

    Returns:
        | str -- the full text, including html.
    """

    # Some sites, such as NYTimes, track which
    # articles have been viewed with cookies.
    # Without cookies, you get thrown into an infinite loop.
    cookies = CookieJar()
    opener = request.build_opener(request.HTTPCookieProcessor(cookies))

    # Spoof a user agent.
    # This can help get around 403 (forbidden) errors.
    req = request.Request(url, headers={'User-Agent': 'Chrome'})

    try:
        html = opener.open(req).read()
    except IncompleteRead as e:
        html = e.partial
    return Document(html).summary()
