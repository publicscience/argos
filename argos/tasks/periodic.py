from argos.tasks import celery

from argos.core.models import Source, Article, Event
from argos.core.membrane import collector
from argos.datastore import db

from datetime import datetime, timedelta

@celery.task
def collect():
    """
    Looks for a source which has not been
    updated in at least an hour
    and fetches new articles for it.
    """
    # Get a source which has not yet been updated
    # and is not currently being updated.
    source = Source.query.filter(Source.updated_at < datetime.utcnow() - timedelta(hours=1) and not Source.updating).first()

    # "Claim" this source,
    # so other workers won't pick it.
    source.updating = True
    db.session.commit()

    try:
        collector.collect(source)
        source.updated_at = datetime.utcnow()

    finally:
        source.updating = False
        db.session.commit()

@celery.task
def cluster_articles(batch_size=20, threshold=0.05):
    """
    Clusters a batch of orphaned articles
    into events.
    """
    articles = Article.query.filter(~Article.events.any()).limit(batch_size).all()
    Event.cluster(articles, threshold=threshold)

@celery.task
def cluster_events(batch_size=20, threshold=0.05):
    """
    Clusters a batch of orphaned events
    into stories.
    """
    events = Event.query.filter(~Event.stories.any()).limit(batch_size).all()
    Story.cluster(events, threshold=threshold)
