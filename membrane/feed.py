"""
Feed
==============

Provides an interface for
accessing RSS feeds.

Example::

    # Print entries from a feed.
    site = 'http://www.polygon.com/'
    feed_url = find_feed(site)
    print(entries(feed_url))
"""

import feedparser
from urllib import request
from http.cookiejar import CookieJar
from . import feedfinder
from brain import trim, sanitize
from readability.readability import Document


def entries(url):
    """
    Parse a feed from the specified url,
    gathering the latest entries.

    Args:
        | url (str)    -- the url of the feed.

    Returns:
        | list -- list of processed latest entries (as dicts).
    """
    # Fetch the feed data.
    data = feedparser.parse(url)

    # Build the entry dicts.
    entries = []
    for entry in data.entries:

        # URL for this entry.
        eurl = entry.links[0].href

        # Complete HTML content for this entry.
        html = fetch_full_text(eurl)

        entries.append({
            'url': eurl,
            'source': url,
            'html': html,
            'text': trim(sanitize(html)),
            'author': entry.author,
            'tags': entry.tags,
            'title': entry.title,
            'published': entry.published,
            'updated': entry.updated
        })

    return entries


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
    html = opener.open(url).read()
    return Document(html).summary()
