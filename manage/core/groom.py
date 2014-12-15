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
            cluster.cluster(articles, snip=False)
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

from datetime import timedelta
class CheckTimeGapsCommand(Command):
    """
    Prints what gaps there are in a set of articles.
    """
    def run(self):
        gaps = []
        with open('/Users/ftseng/Downloads/argos_corpora/articles.json', 'r') as f:
            articles = json.load(f)
            dates = [datetime.fromtimestamp(a['created_at']['$date']/1000) for a in articles]
            dates.sort()

        # Starting from 2013-05-02
        # (this is about when collecting started, although some older articles were somehow collected as well)
        start_date = datetime.strptime('2013-05-02', '%Y-%m-%d')
        dates = [d for d in dates if d > start_date]

        # Calculate timedeltas and only keep those >= than a day.
        last_date = dates[0]
        for date in dates[1:]:
            td = date - last_date
            if td >= timedelta(days=1):
                gaps.append((last_date, date, td))
            last_date = date


        # Sort gaps by size
        gaps.sort(key=lambda x: x[2], reverse=True)

        print('Gaps:')
        days = []
        for gap in gaps:
            print('From {0} to {1}, {2}'.format(gap[0], gap[1], gap[2]))
            # For each day in the gap:
            for d in daterange(gap[0], gap[1]):
                days.append(d)
        print('Missing days: {0}'.format(len(days)))

def daterange(start_date, end_date):
    for n in range(int ((end_date - start_date).days)):
        yield start_date + timedelta(n)
