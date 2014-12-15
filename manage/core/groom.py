"""
Groom
=====

Various management commands which
are for fixes and touch ups and so on.

These aren't really meant to be permanent;
i.e. you should solve the underlying issues
rather than rely on these commands. But they
are temporary fixes.
"""

import os
import shutil
from time import time

from flask.ext.script import Command, Option

from argos.datastore import db
from argos.core.brain import cluster
from argos.core.models import Article, Event
from argos.conf import APP
from argos.util.progress import Progress

class ReclusterCommand(Command):
    """
    This will reconstruct the ENTIRE hierarchy.
    You'd really only want to do this if you changed the clustering
    parameters and want to reconstruct the hierarchy with the new params.

    Depending on how many articles you have, this may take a TON of time.
    """
    def run(self):
        path = APP['CLUSTERING']['hierarchy_path']
        path = os.path.expanduser(path)

        if os.path.exists(path):
            print('Backing up existing hierarchy...')
            shutil.move(path, path + '.bk')

        # Delete existing events.
        events = Event.query.delete()

        articles = Article.query.filter(Article.node_id != None).all()

        # Reset node associations.
        print('Resetting article-node associations...')
        for article in articles:
            article.node_id = None
        db.session.commit()

        print('Reconstructing the hierarchy...')
        start_time = time()

        total = Article.query.count()

        p = Progress()

        # Cluster articles in batches of 1000, for memory's sake.
        batch_size = 100
        articles, remaining = get_unclustered_articles(batch_size)
        p.print_progress((total-remaining)/(total - 1))
        while articles:
            cluster.cluster(articles)
            articles, remaining = get_unclustered_articles(batch_size)
            p.print_progress((total-remaining)/(total - 1))

        elapsed_time = time() - start_time
        print('Clustered {0} articles in {1}.'.format(len(articles), elapsed_time))
        print('Reconstruction done!')

def get_unclustered_articles(batch_size):
    articles = Article.query.filter(Article.node_id == None).order_by(Article.created_at.asc()).limit(batch_size).all()
    remaining = Article.query.filter(Article.node_id == None).count()
    return articles, remaining

class PreviewEventsCommand(Command):
    option_list = (
        Option(dest='num_events', type=int),
    )
    def run(self, num_events):
        for e in Event.query.limit(num_events).all():
            print(e.title)
            for m in e.members:
                print('\t{0}'.format(m.title))
