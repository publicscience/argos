from argos.datastore import db, join_table
from argos.core.models import Concept, Event
from argos.core.models.concept import BaseConceptAssociation
from argos.core.models.cluster import Cluster
from argos.core.brain.summarizer import multisummarize

import itertools
from nltk.tokenize import sent_tokenize

from argos.util.logger import logger
from argos.conf import APP

logr = logger('STORY_CLUSTERING')

if APP['DEBUG']:
    logr.setLevel('DEBUG')
else:
    logr.setLevel('ERROR')

stories_events = join_table('stories_events', 'story', 'event')
stories_mentions = join_table('stories_mentions', 'story', 'alias')

class StoryConceptAssociation(BaseConceptAssociation):
    __backref__     = 'story_associations'
    story_id        = db.Column(db.Integer, db.ForeignKey('story.id', ondelete='CASCADE', onupdate='CASCADE'), primary_key=True)

class Story(Cluster):
    __tablename__   = 'story'
    __members__     = {'class_name': 'Event', 'secondary': stories_events, 'backref_name': 'stories'}
    __concepts__    = {'association_model': StoryConceptAssociation, 'backref_name': 'story'}
    __mentions__    = {'secondary': stories_mentions, 'backref_name': 'stories'}

    @property
    def events(self):
        """
        Convenience :)
        """
        return self.members.order_by(Event.created_at.desc()).all()

    @events.setter
    def events(self, value):
        self.members = value

    def events_before(self, dt):
        """
        Returns all events in this story
        created *at or before* the specified datetime.
        """
        return self.members.filter(Event.created_at <= dt).all()

    def events_after(self, dt):
        """
        Returns all events in this story
        created *at or after* the specified datetime.
        """
        return self.members.filter(Event.created_at >= dt).all()

    def events_by_date(self, sort='desc'):
        """
        Returns all events in this story,
        grouped by created at dates.
        """
        if sort == 'asc':
            events = self.members.order_by(Event.created_at.asc()).all()
        else:
            events = self.members.order_by(Event.created_at.desc()).all()
        results = []
        for date, group in itertools.groupby(events, lambda x: x.created_at.date()):
            results.append((date, list(group)))
        return results

    @property
    def images(self):
        """
        Gets images from its members.
        """
        return [member.image for member in self.members if member.image is not None]

    @property
    def summary_sentences(self):
        """
        Breaks up a summary back into its
        original sentences (as a list).
        """
        return sent_tokenize(self.summary)

    def summarize(self):
        """
        Generate a summary for this cluster.
        """
        if self.members.count() == 1:
            self.summary = self.members[0].summary
        else:
            self.summary = ' '.join(multisummarize([m.summary for m in self.members]))
        return self.summary
