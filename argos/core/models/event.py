from argos.datastore import db, join_table
from argos.core.models.cluster import Cluster
from argos.core.models.concept import BaseConceptAssociation
from argos.core.brain import summarizer

from itertools import chain
from datetime import datetime
from math import log
from sqlalchemy import event, inspect
from nltk.tokenize import sent_tokenize

import galaxy as gx

events_articles = join_table('events_articles', 'event', 'article')
events_mentions = join_table('events_mentions', 'event', 'alias')

class EventConceptAssociation(BaseConceptAssociation):
    __backref__     = 'event_associations'
    event_id        = db.Column(db.Integer, db.ForeignKey('event.id', ondelete='CASCADE', onupdate='CASCADE'), primary_key=True)

class Event(Cluster):
    __tablename__   = 'event'
    __members__     = {'class_name': 'Article', 'secondary': events_articles, 'backref_name': 'events'}
    __concepts__    = {'association_model': EventConceptAssociation, 'backref_name': 'event'}
    __mentions__    = {'secondary': events_mentions, 'backref_name': 'events'}
    active          = db.Column(db.Boolean, default=True)
    raw_score       = db.Column(db.Float, default=0.0)
    _score          = db.Column(db.Float, default=0.0)

    @classmethod
    def all_active(cls):
        """
        Returns all active events.
        """
        return cls.query.filter_by(active=True).all()

    @property
    def articles(self):
        """
        Convenience :)
        """
        return self.members.all()

    @property
    def num_articles(self):
        return self.members.count()

    @articles.setter
    def articles(self, value):
        self.members = value

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
        data = [{'sentence': sent} for sent in sent_tokenize(self.summary)]
        for d in data:
            article = next((a for a in self.members if d['sentence'] in ' '.join([a.title, a.text])), None)
            if article is not None:
                d['source'] = article.source.name
                d['url']    = article.ext_url
            else:
                d['source'] = None
                d['url']    = None
        return data

    @property
    def top_concepts(self):
        return self.concepts[:10]

    @property
    def score(self):
        """
        Returns the event's score,
        caculating a fresh value on the fly
        and setting it on the event.
        """
        self._score = self.calculate_score()
        return self._score

    def calculate_score(self):
        """
        Calculates a score for the event,
        based on its articles' scores (its `raw_score`).

        Its score is modified by the oldness of this event.

        Currently this uses the Reddit 'hot' formula,
        see: http://amix.dk/blog/post/19588
        """
        # Calculate the raw score if it doesn't yet exist.
        if not self.raw_score:
            self.raw_score = sum([member.score for member in self.members])
        score = self.raw_score
        epoch = datetime(1970, 1, 1)
        td = self.updated_at - epoch
        epoch_seconds = td.days * 86400 + td.seconds + (float(td.microseconds) / 1000000)
        order = log(max(abs(score), 1), 10)
        sign = 1 if score > 0 else -1 if score < 0 else 0
        seconds = epoch_seconds - 1134028003
        return round(order + sign * seconds / 45000, 7)

    def update_score(self):
        # Calculate the raw score.
        self.raw_score = sum([member.score for member in self.members])

        # Cache a score.
        self._score = self.calculate_score()

    @property
    def member_concept_slugs(self):
        """
        The aggregate of all this event's
        articles' concepts
        """
        if not hasattr(self, '_mem_slugs') or self._mem_slugs is None:
            concepts = [' '.join(a.concept_slugs) for a in self.articles]
            self._mem_slugs = ' '.join(concepts)
        return self._mem_slugs

    @property
    def text(self):
        """
        The aggregate of all of this event's
        articles' texts.
        """
        if not hasattr(self, '_text') or self._text is None:
            texts = [' '.join([a.title, a.text]) for a in self.articles]
            self._text = ' '.join(texts)
        return self._text

    def summarize(self):
        """
        Generate a summary for this cluster.
        """
        if self.members.count() == 1:
            member = self.members[0]
            summary_sentences = summarizer.summarize(member.title, member.text)
            self.summary = ' '.join(summary_sentences)
        else:
            summary_sentences = summarizer.multisummarize([m.text for m in self.members])
            self.summary = ' '.join(summary_sentences)
        return self.summary

@event.listens_for(Event, 'before_update')
def receive_before_update(mapper, connection, target):
    # Only make these changes if the articles have changed.
    if inspect(target).attrs.members.history.has_changes():
        target.update_score()
        target.updated_at = datetime.utcnow()

        # Reset calculated values.
        target._text = None
        target._mem_slugs = None

@event.listens_for(Event, 'before_insert')
def receive_before_insert(mapper, connection, target):
    target.update_score()
    target.updated_at = datetime.utcnow()

