"""
Feed
==============

Provides an interface for
accessing RSS feeds.
"""

import feedparser
import feedfinder
import urllib
from sanitizer import sanitize
from readability.readability import Document

class Feed:
    """
    Provides an interface for
    accessing RSS feeds.
    """

    def __init__(self):
        """
        Create a new interface.
        """

    def parse(self, url):
        """
        Parse a feed from the specified url.

        Args:
            | url (str)    -- the url of the feed.

        Returns:
            | dict -- the feed XML response parsed to a dict.
        """
        data = feedparser.parse(url)

        for entry in data.entries:
            entry_url = entry.links[0].href
            full_text = self._fetch_full_text(entry_url)
            clean_text = ' '.join(sanitize(full_text).split())
            print clean_text

    def get_feed(self, url):
        """
        Find the RSS feed url for a site.

        Args:
            | url (str)    -- the url of the site to search.

        Returns:
            | str -- the discovered feed url.
        """
        return feedfinder.feed(url)

    def _fetch_full_text(self, url):
        """
        Fetch the full content for a feed entry url.

        Args:
            | url (str)    -- the url of the entry.

        Returns:
            | str -- the full text.
        """
        html = urllib.urlopen(url).read()
        return Document(html).summary()
