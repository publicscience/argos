from argos.tasks import celery, notify

from argos.core.brain import cluster
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

    if feed:
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

        notify('Collecting for feed {0} is complete. Collected {1} new articles.'.format(feed.ext_url))

@celery.task
def cluster_articles():
    """
    Clusters a batch of orphaned articles
    from the past few days into events.
    """
    articles = Article.query.filter(~Article.events.any(), Article.created_at < datetime.utcnow() - timedelta(days=2)).all()
    if articles:
        cluster.cluster(articles)
        notify('Clustering articles successful.')
