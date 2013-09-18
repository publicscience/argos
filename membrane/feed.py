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
import urllib
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
        html = self.fetch_full_text(eurl)

        entries.append({
            'url': eurl,
            'html': html,
            'text': trim(sanitize(html)),
            'author': entry.author,
            'published': entry.published
        })

    return entries


def find_feed(url):
    """
    Find the RSS feed url for a site.

    Args:
        | url (str)    -- the url of the site to search.

    Returns:
        | str -- the discovered feed url.
    """
    return feedfinder.feed(url)


def fetch_full_text(url):
    """
    Fetch the full content for a feed entry url.

    Args:
        | url (str)    -- the url of the entry.

    Returns:
        | str -- the full text, including html.
    """
    html = urllib.urlopen(url).read()
    return Document(html).summary()
