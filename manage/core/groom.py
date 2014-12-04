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
from flask.ext.script import Command

from argos.datastore import db
from argos.core.brain import cluster
from argos.core.models import Article, Event
from argos.conf import APP

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

        # Reload the hierarchy.
        cluster.load_hierarchy()

        articles = Article.query.all()

        # Reset node associations.
        print('Resetting article-node associations...')
        for article in articles:
            article.node_id = None
        db.session.commit()

        print('Reconstructing the hierarchy...')
        cluster.cluster(articles)
        print('Reconstruction done!')

import json
from datetime import datetime
from unittest.mock import patch
from argos.util.progress import progress_bar

class BackClusterCommand(Command):
    def run(self):
        # Patch out saving images to S3.
        patcher = patch('argos.util.storage.save_from_url', autospec=True, return_value='https://i.imgur.com/Zf9mXlj.jpg')
        patcher.start()

        path = APP['CLUSTERING']['hierarchy_path']
        path = os.path.expanduser(path)

        if os.path.exists(path):
            print('Backing up existing hierarchy...')
            shutil.move(path, path + '.bk')

        print('Resetting the database...')
        db.reflect()
        db.drop_all()
        db.create_all()

        with open('/Users/ftseng/all_feeds.json', 'r') as f:
            feeds = json.load(f)

        with open('manage/core/data/sources.json', 'r') as f:
            valid_feeds = []
            for source, fs in json.load(f).items():
                valid_feeds += fs

        feeds = [f['_id']['$oid'] for f in feeds if f['ext_url'] in valid_feeds]

        with open('/Users/ftseng/all_articles_cleaned.json', 'r') as f:
            all_articles = json.load(f)

        filtered_articles = [a for a in all_articles if a['feed']['$oid'] in feeds]

        print('Using {0} articles...'.format(len(filtered_articles)))

        filtered_articles = filtered_articles[:2000]

        print('Building articles...')
        articles = []
        for i, a in enumerate(filtered_articles):
            article = Article(
                ext_url=a['ext_url'],
                source=None,  # tmp
                feed=None,    # tmp
                html=None,    # not saved
                text=a['text'],
                authors=[], # tmp
                tags=[],    # not saved
                title=a['title'],
                created_at=datetime.fromtimestamp(a['created_at']['$date']/1000),
                updated_at=datetime.fromtimestamp(a['updated_at']['$date']/1000),
                image=a['image'],
                score=0       # don't bother calculating
            )
            articles.append(article)
            db.session.add(article)
            progress_bar(i/len(filtered_articles) * 100)

        articles.sort(key=lambda x: x.created_at)

        db.session.commit()
        patcher.stop()

        print(len(articles))

        print('Clustering articles...')
        cluster.cluster(articles)
        print('Done!')


class EventsCommand(Command):
    def run(self):
        for e in Event.query.all():
            print(e.title)
            for m in e.members:
                print('\t{0}'.format(m.title))
