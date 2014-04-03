from argos.core.models import Event, Story
from argos.core.membrane import collector

from flask.ext.script import Command

from datetime import datetime, timedelta

from argos.util.logger import logger
logger = logger(__name__)

class PonderCommand(Command):
    """
    Collects the latest articles from all sources,
    clusters them into events, and
    clusters events from a recent timeframe into stories.
    """
    def run(self):
        ponder()

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
        for articles in collector.collect():
            Event.cluster(articles, threshold=0.05)

        # Cluster events from the past two weeks.
        # (two weeks is an arbitrary number, will need to choose a time frame)
        recent_events = Event.query.filter(Event.updated_at > datetime.utcnow() - timedelta(days=14)).all()
        Story.cluster(recent_events, threshold=0.05)
    except Exception:
        logger.exception('Encountered an error while pondering!')
        raise
