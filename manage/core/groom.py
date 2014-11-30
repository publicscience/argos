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
from argos.core.models import Article
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
