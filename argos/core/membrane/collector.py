"""
Collector
==============

A corpus builder, for the sake of collecting
articles for training and/or testing.
"""

from argos.datastore import db
from argos.core.models import Article
from argos.core.membrane import evaluator, extractor

from dateutil.parser import parse
from urllib import error
import feedparser

from xml.sax._exceptions import SAXException
from http.client import BadStatusLine

# Logging.
from argos.util.logger import logger
logger = logger(__name__)

def collect(feed):
    """
    Fetch articles from the specified feed,
    and save to db.
    """

    try:
        logger.info('Fetching from {0}...'.format(feed.ext_url))

        def commit_article(article):
            db.session.add(article)

        get_articles(feed, commit_article)
        db.session.commit()

    except SAXException as e:
        # Error with the feed, make a note.
        logger.info('Error fetching from {0}.'.format(feed.ext_url))
        feed.errors += 1
        db.session.commit()


def get_articles(feed, fn):
    """
    Parse the specified feed,
    gathering the latest new articles.

    If an article matches one that already exists,
    it is skipped.

    The minimum length of an entry is
    500 characters. Anything under will be ignored.

    This will silently skip articles for which the full text
    can't be retrieved (i.e. if it returns 404).

    Some feeds, for whatever reason, do not include a `published`
    date in their entry data. In which case, it is left as an
    empty string.

    Args:
        | feed (Feed)    -- the feed to fetch from.
        | fn (Callable)  -- function to use an article
    """
    # Fetch the feed data.
    data = feedparser.parse(feed.ext_url)

    # If the `bozo` value is anything
    # but 0, there was an error parsing (or connecting) to the feed.
    if data.bozo:
        # Some errors are ok.
        if not isinstance(data.bozo_exception, feedparser.CharacterEncodingOverride) and not isinstance(data.bozo_exception, feedparser.NonXMLContentType):
            raise data.bozo_exception

    for entry in data.entries:

        # URL for this entry.
        url = entry['links'][0]['href']

        # Check for an existing Article.
        # If one exists, skip.
        if Article.query.filter_by(ext_url=url).count():
            continue

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

        if entry_data is None:
            continue

        full_text = entry_data.cleaned_text

        # Skip over entries that are too short.
        if len(full_text) < 400:
            continue

        url = entry_data.canonical_link or url
        published = parse(entry.get('published')) if entry.get('published') else entry_data.publish_date
        updated = parse(entry.get('updated')) if entry.get('updated') else published
        title = entry.get('title', entry_data.title)

        # Secondary check for an existing Article,
        # by checking the title and source.
        existing = Article.query.filter_by(title=title).first()
        if existing and existing.source == feed.source:
            continue

        # Download and save the top article image.
        image_url = extractor.extract_image(entry_data, filename=hash(url))

        fn(Article(
            ext_url=url,
            source=feed.source,
            feed=feed,
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
