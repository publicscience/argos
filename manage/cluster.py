from argos.core.models import Article, Event, Story

from flask.ext.script import Command

import math

from argos.util.logger import logger
logger = logger(__name__)

class ClusterArticlesCommand(Command):
    def run(self):
        cluster_articles()

class ClusterEventsCommand(Command):
    def run(self):
        cluster_events()

def cluster_articles():
    """
    Batch cluster all articles => events
    which do not already belong to events.
    """
    total_articles = Article.query.filter(not Article.events).count()

    if total_articles:
        logger.info('Clustering {0} orphaned articles...'.format(total_articles))

        # Cluster in batches to reduce memory footprint.
        per_page = 50
        pages = math.ceil(total_articles/per_page)

        logger.info('Clustering in {0} batches...'.format(pages))

        for page in range(1, pages):
            logger.info('Clustering {0}% complete.'.format(page/pages * 100))
            # Pages are 1-indexed.
            articles = Article.query.filter(not Article.events).paginate(page, per_page=per_page).items
            Event.cluster(articles, threshold=0.1)

        logger.info('Clustering complete.')
    else:
        logger.info('No orphaned articles to cluster.')

def cluster_events():
    """
    Batch cluster all events => stories
    which do not already belong to stories.
    """
    total_events = Event.query.filter(not Event.stories).count()

    if total_events:
        logger.info('Clustering {0} orphaned events...'.format(total_events))

        per_page = 20
        pages = math.ceil(total_events/per_page)

        logger.info('Clustering in {0} batches...'.format(pages))

        for page in range(1, pages):
            logger.info('Clustering {0}% complete.'.format(page/pages * 100))
            events = Event.query.filter(not Event.stories).paginate(page, per_page=per_page).items

            Story.cluster(events, threshold=0.1)

        logger.info('Clustering complete.')
    else:
        logger.info('No orphaned events to cluster.')
