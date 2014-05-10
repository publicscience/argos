from argos.datastore import db
from argos.core.models.cluster import Cluster
from argos.core.models.concept import BaseConceptAssociation
from argos.core.brain.cluster import cluster
from argos.core.brain import summarize, sentences

from argos.util.logger import logger

from datetime import datetime
from math import log
from sqlalchemy import event, inspect

events_articles = db.Table('events_articles',
        db.Column('event_id', db.Integer, db.ForeignKey('event.id', ondelete='CASCADE', onupdate='CASCADE'), primary_key=True),
        db.Column('article_id', db.Integer, db.ForeignKey('article.id', ondelete='CASCADE', onupdate='CASCADE'), primary_key=True)
)

events_mentions = db.Table('events_mentions',
        db.Column('alias_id', db.Integer, db.ForeignKey('alias.id', ondelete='CASCADE', onupdate='CASCADE')),
        db.Column('event_id', db.Integer, db.ForeignKey('event.id', ondelete='CASCADE', onupdate='CASCADE'))
)

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
        return sentences(self.summary)

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

    def summarize(self):
        """
        Generate a summary for this cluster.
        """
        if self.members.count() == 1:
            member = self.members[0]
            self.summary = ' '.join(summarize.summarize(member.title, member.text))
        else:
            self.summary = ' '.join(summarize.multisummarize([m.text for m in self.members]))
        return self.summary

    @staticmethod
    def recluster(articles, threshold=0.7, debug=False):
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
        Event.cluster(articles, threshold=threshold, debug=debug)

    @staticmethod
    def cluster(articles, threshold=0.7, debug=False):
        """
        Clusters a set of articles
        into existing events (or creates new ones).

        Args:
            | articles (list)       -- the Articles to cluster
            | threshold (float)     -- the similarity threshold for qualifying a cluster
        """
        log = logger('EVENT_CLUSTERING')
        if debug:
            log.setLevel('DEBUG')
        else:
            log.setLevel('ERROR')

        updated_clusters = []
        active_clusters = Event.query.filter_by(active=True).all()
        now = datetime.utcnow()

        for article in articles:
            # Select candidate clusters,
            # i.e. active clusters which share at least one concept with this article.
            a_cons = [concept.slug for concept in article.concepts]
            candidate_clusters = []
            for c in active_clusters:
                c_cons = [concept.slug for concept in c.concepts]
                if set(c_cons).intersection(a_cons):
                    candidate_clusters.append(c)

            selected_cluster = cluster(article, candidate_clusters, threshold=threshold, logger=log)

            # If no selected cluster was found, then create a new one.
            if not selected_cluster:
                log.debug('No qualifying clusters found, creating a new cluster.')
                selected_cluster = Event([article])
                db.session.add(selected_cluster)

                # The new cluster is also an active cluster.
                active_clusters.append(selected_cluster)

            updated_clusters.append(selected_cluster)

        for clus in active_clusters:
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
        # Calculate the raw score.
        target.raw_score = sum([member.score for member in target.members])

        # Cache a score.
        target._score = target.calculate_score()

        target.updated_at = datetime.utcnow()

@event.listens_for(Event, 'before_insert')
def receive_before_insert(mapper, connection, target):
    # Calculate the raw score.
    target.raw_score = sum([member.score for member in target.members])

    # Cache a score.
    target._score = target.calculate_score()

    target.updated_at = datetime.utcnow()

