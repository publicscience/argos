"""
Collector
==============

A corpus builder, for the sake of collecting
articles for training and/or testing.
"""

from membrane import feed
from adipose import Adipose
from zlib import adler32 as hash

# Logging.
from logger import logger
logger = logger(__name__)

def collect():
    """
    Fetches entries and processes them.
    """
    articles = fetch()
    docs = [article.text for article in articles]

def fetch():
    """
    Fetch entries from the sources,
    and save (or update) to db.
    """
    results = []
    articles_db = _articles_db()
    sources_db = _sources_db()

    logger.info('Fetching articles...')

    # Fetch entries for each source
    for source in sources():
        feed_url = source['url']
        try:
            logger.info('Fetching from %s...' % feed_url)
            articles = feed.entries(feed_url)

            # Create (unique-ish) ids for each article,
            # then save (or update).
            for article in articles:
                id = hash((article['title'] + article['published']).encode('utf-8'))
                articles_db.update({'_id': id}, {'$set': article})

                article['_id'] = id
                results.append(article)

        except feed.SAXException as e:
            # Error with the feed, make a note.
            logger.info('Error fetching from %s.' % feed_url)
            source['errors'] = source.get('errors', 0) + 1
            sources_db.save(source)

    logger.info('Finished fetching articles.')

    articles_db.close()
    sources_db.close()

    return results


def sources():
    """
    Get the feed sources data.
    """
    sources = _sources_db()
    return [source for source in sources.all()]


def add_source(url):
    """
    Add a new source.

    Args:
        | url (str)     -- where to look for the feed,
                           or the feed itself.
    """
    sources = _sources_db()
    feed_url = feed.find_feed(url)
    doc = {'url': feed_url}
    sources.update(doc, {'$set': doc})
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
    sources = _sources_db()
    feed_url = feed.find_feed(url)
    sources.remove({'url': feed_url})
    sources.close()

    # If specified, delete articles associated with
    # this source.
    if delete_articles:
        articles = _articles_db()
        articles.remove({'source': feed_url})
        articles.close()


def collect_sources(url):
    """
    Collects feed sources from the specified url,
    and adds them.

    Args:
        | url (str)     -- where to look for feeds.
    """
    feeds = feed.find_feeds(url)
    for f in feeds:
        add_source(f)


def _sources_db():
    return Adipose('corpus', 'sources')

def _articles_db():
    return Adipose('corpus', 'articles')

