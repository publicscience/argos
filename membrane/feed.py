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

    Example::

        # Print entries from a feed.
        site = 'http://www.polygon.com/'
        f = Feed()
        feed_url = f.find_feed(site)
        print f.entries(feed_url)
    """

    def __init__(self):
        """
        Create a new interface.
        """

    def entries(self, url):
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
            html = self._fetch_full_text(eurl)

            entries.append({
                'url': eurl,
                'html': html,
                'text': ' '.join(sanitize(html).split()),
                'author': entry.author,
                'published': entry.published
            })

        return entries

    def find_feed(self, url):
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
            | str -- the full text, including html.
        """
        html = urllib.urlopen(url).read()
        return Document(html).summary()
