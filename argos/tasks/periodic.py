from argos.tasks import celery, notify

from argos.core.models import Feed, Article, Event, Story
from argos.core.membrane import collector
from argos.datastore import db

from datetime import datetime, timedelta

# Logging.
from argos.util.logger import logger
logger = logger(__name__)

@celery.task
def collect():
    """
    Looks for a source which has not been
    updated in at least an hour
    and fetches new articles for it.
    """
    # Get a feed which has not yet been updated
    # and is not currently being updated.
    feed = Feed.query.filter(Feed.updated_at < datetime.utcnow() - timedelta(hours=1), ~Feed.updating).first()

    # "Claim" this feed,
    # so other workers won't pick it.
    feed.updating = True
    db.session.commit()

    try:
        collector.collect(feed)
        feed.updated_at = datetime.utcnow()

    except Exception:
        logger.exception('Exception while collecting for feed {0}'.format(feed.ext_url))
        raise

    finally:
        feed.updating = False
        db.session.commit()
        notify('Collecting for feed {0} is complete.'.format(feed.ext_url))

@celery.task
def cluster_articles(batch_size=5, threshold=0.05):
    """
    Clusters a batch of orphaned articles
    into events.
    """
    articles = Article.query.filter(~Article.events.any()).limit(batch_size).all()
    Event.cluster(articles, threshold=threshold)
    notify('Clustering articles successful.')

@celery.task
def cluster_events(batch_size=5, threshold=0.05):
    """
    Clusters a batch of orphaned events
    into stories.
    """
    events = Event.query.filter(~Event.stories.any()).limit(batch_size).all()
    Story.cluster(events, threshold=threshold)
    notify('Clustering events successful.')
