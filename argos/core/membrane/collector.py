"""
Collector
==============

A corpus builder, for the sake of collecting
articles for training and/or testing.
"""

from argos.datastore import db
from argos.core.models import Source, Article, Event, Story
from argos.core.membrane import evaluator, extractor

from datetime import datetime, timedelta
from dateutil.parser import parse
from urllib import error
import feedparser

from xml.sax._exceptions import SAXException
from http.client import BadStatusLine

# Logging.
from argos.util.logger import logger
logger = logger(__name__)

def collect():
    """
    Fetch articles from the sources,
    and save to db.

    This is a generator which yields a list
    of new Articles per Source.
    """

    # Fetch entries for each source
    for source in Source.query.all():
        try:
            logger.info('Fetching from {0}...'.format(source.ext_url))
            new_articles = get_articles(source)

            for article in new_articles:
                db.session.add(article)
            db.session.commit()

            yield new_articles

        except SAXException as e:
            # Error with the feed, make a note.
            logger.info('Error fetching from {0}.'.format(source.ext_url))
            source.errors += 1
            db.session.commit()

            yield []


def ponder():
    """
    This is a simple job
    which is meant to be run regularly.

    It collects the latest articles from
    all the sources and clusters them into events,
    and also clusters events from a recent timeframe
    into stories.
    """
    try:
        logger.info('Pondering...')

        # Cluster each set of articles
        for articles in collect():
            Event.cluster(articles, threshold=0.05)

        # Cluster events from the past two weeks.
        # (two weeks is an arbitrary number, will need to choose a time frame)
        recent_events = Event.query.filter(Event.updated_at > datetime.utcnow() - timedelta(days=14)).all()
        Story.cluster(recent_events, threshold=0.05)
    except Exception:
        logger.exception('Encountered an error while pondering!')
        raise


def get_articles(source):
    """
    Parse a feed from the specified source,
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
        | source (Source)    -- the source to fetch from.

    Returns:
        | list -- list of latest new Articles.
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


