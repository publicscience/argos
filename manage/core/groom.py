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

from argos.core.models import Article, Event, Story

from flask.ext.script import Command, Option

class ReclusterCommand(Command):
    option_list = (
        Option(dest='threshold', type=float),
    )
    def run(self, threshold):
        print('Reclustering articles...')
        articles = Article.query.all()
        Event.recluster(articles, threshold=threshold)
        print('Reclustering articles successful.')

        print('Reclustering events...')
        events = Event.query.all()
        Story.recluster(events, threshold=threshold)
        print('Reclustering events successful.')
