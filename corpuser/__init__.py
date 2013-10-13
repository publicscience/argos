"""
Corpuser
==============

A corpus builder, for the sake of collecting
articles for training and/or testing.
"""

from membrane import feed
from adipose import Adipose
import zlib.adler32 as hash

def fetch():
    """
    Fetch entries from the sources,
    and save (or update) to db.
    """
    db = Adipose('corpus', 'articles')

    # Load sources.
    sources = sources()

    # Fetch entries for each source
    for source in sources:
        articles = feed.entries(source['url'])

        # Create (unique-ish) ids
        # for each article,
        # then save (or update).
        for article in articles:
            id = hash((article.title + article.published).encode('utf-8'))
            db.update({'_id': id}, {'$set': article})
    articles.close()


def sources():
    """
    Get the feed sources data.
    """
    sources = Adipose('corpus', 'sources')
    return [source for source in sources.all()]


def add_source(url):
    """
    Add a new source.

    Args:
        | url (str)     -- where to look for the feed,
                           or the feed itself.
    """
    sources = Adipose('corpus', 'sources')
    feed_url = feed.find_feed(url)
    sources.add({'url': feed_url})
    sources.close()


def remove_source(url, delete_articles=False):
    """
    Remove a source.

    Args:
        | url (str)                 -- where to look for the feed,
                                       or the feed itself.
        | delete_articles (bool)    -- whether or not to delete articles
                                       from this source.
    """
    sources = Adipose('corpus', 'sources')
    feed_url = feed.find_feed(url)
    sources.remove({'url': feed_url})
    sources.close()

    # If specified, delete articles associated with
    # this source.
    if delete_articles:
        articles = Adipose('corpus', 'articles')
        articles.remove({'source': feed_url})
    articles.close()


