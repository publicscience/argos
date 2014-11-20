from argos.datastore import db, join_table
from argos.core.models.cluster import Cluster
from argos.core.models.concept import BaseConceptAssociation
from argos.core import brain
from argos.core.brain import summarizer
from argos.core.brain.cluster import cluster

from itertools import chain
from datetime import datetime
from math import log
from sqlalchemy import event, inspect
from difflib import SequenceMatcher

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

    @property
    def articles(self):
        """
        Convenience :)
        """
        return self.members.all()

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
        return brain.sentences(self.summary)

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

    def vectorize(self):
        """
        Returns a tuple of vectors representing this event.

        Events are represented by:
            (bag of words vector, concepts vector)
        """
        if not hasattr(self, 'vectors') or self.vectors is None:
            bow_vec = brain.vectorizer.vectorize(self.text)
            ent_vec = brain.conceptor.vectorize(self.member_concept_slugs)
            self.vectors = [bow_vec, ent_vec]
        return self.vectors

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
            self.summary = ' '.join(summarizer.summarize(member.title, member.text))
        else:
            self.summary = ' '.join(summarizer.multisummarize([m.text for m in self.members]))
        return self.summary

    @staticmethod
    def recluster(articles, threshold=0.7):
        """
        Reclusters a set of articles,
        resetting their existing event membership.
        """
        for article in articles:
            article.events = []
        db.session.commit()

        # Prune childless events.
        # This can probably be handled by SQLAlchemy through some configuration...
        for event in Event.query.filter(~Event.members.any()).all():
            db.session.delete(event)
        db.session.commit()

        # Re-do the clustering.
        Event.cluster(articles, threshold=threshold)

    @staticmethod
    def cluster(articles, threshold=0.7):
        """
        Clusters a set of articles
        into existing events (or creates new ones).

        Args:
            | articles (list)       -- the Articles to cluster
            | threshold (float)     -- the similarity threshold for qualifying a cluster
        """
        now = datetime.utcnow()
        active = Event.query.filter_by(active=True).all()

        existing_clusters = [event.members for event in active]
        existing_articles = list(chain.from_iterable(existing_clusters))

        articles = articles + existing_articles
        vectors = [a.vectors for a in articles]
        clusters = cluster(vectors, articles)

        # Convert to sorted lists of ids for comparison.
        existing_clusters_ = [sorted([a.id for a in cluster.members]) for cluster in existing_clusters]
        clusters_ = [sorted([a.id for a in cluster.members]) for cluster in clusters_]

        #for cluster in clusters_:
            #for excluster in existing_clusters_:

        for clus in active:
            # Mark expired clusters inactive.
            if (now - clus.updated_at).days > 3:
                clus.active = False
            else:
                clus.update()

        db.session.commit()
        return updated_clusters

@event.listens_for(Event, 'before_update')
def receive_before_update(mapper, connection, target):
    # Only make these changes if the articles have changed.
    if inspect(target).attrs.members.history.has_changes():
        target.update_score()
        target.updated_at = datetime.utcnow()

        # Reset calculated values.
        target.vectors = None
        target._text = None
        target._mem_slugs = None

@event.listens_for(Event, 'before_insert')
def receive_before_insert(mapper, connection, target):
    target.udpate_score()
    target.updated_at = datetime.utcnow()

