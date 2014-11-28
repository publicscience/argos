from flask.ext.script import Command

from argos.core.models import Article, Event, Story

class GutcheckCommand(Command):
    def run(self):
        print('There are {0} articles.'.format(Article.query.count()))
        print('There are {0} events.'.format(Event.query.count()))
        print('There are {0} stories.'.format(Story.query.count()))
