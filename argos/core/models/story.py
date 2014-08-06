from argos.datastore import db, join_table
from argos.core.models import Concept, Event
from argos.core.models.concept import BaseConceptAssociation
from argos.core.models.cluster import Cluster
from argos.core.brain import sentences
from argos.core.brain.cluster import cluster
from argos.core.brain.summarizer import multisummarize

import itertools

from argos.util.logger import logger

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
        return sentences(self.summary)

    def summarize(self):
        """
        Generate a summary for this cluster.
        """
        if self.members.count() == 1:
            self.summary = self.members[0].summary
        else:
            self.summary = ' '.join(multisummarize([m.summary for m in self.members]))
        return self.summary

    @staticmethod
    def recluster(events, threshold=0.7, debug=False):
        """
        Reclusters a set of events,
        resetting their existing story membership.
        """
        for event in events:
            event.stories = []
        db.session.commit()

        # Prune childless stories.
        # This can probably be handled by SQLAlchemy through some configuration...
        for story in Story.query.filter(~Story.members.any()).all():
            db.session.delete(story)
        db.session.commit()

        # Re-do the clustering.
        Story.cluster(events, threshold=threshold, debug=debug)

    @staticmethod
    def cluster(events, threshold=0.7, debug=False):
        """
        Clusters a set of events
        into existing stories (or creates new ones).

        Args:
            | events (list)         -- the Events to cluster
            | threshold (float)     -- the similarity threshold for qualifying a cluster
            | debug (bool)          -- will log clustering info if True

        Returns:
            | clusters (list)       -- the list of updated clusters
        """
        log = logger('STORY_CLUSTERING')
        if debug:
            log.setLevel('DEBUG')
        else:
            log.setLevel('ERROR')

        updated_clusters = []

        for event in events:
            # Find stories which have some matching concepts with this event.
            candidate_clusters = Story.query.filter(Concept.slug.in_(event.concept_slugs)).all()

            # Cluster this event.
            selected_cluster = cluster(event, candidate_clusters, threshold=threshold, logger=log)

            # If no selected cluster was found, then create a new one.
            if not selected_cluster:
                log.debug('No qualifying clusters found, creating a new cluster.')
                selected_cluster = Story([event])
                db.session.add(selected_cluster)
                db.session.commit() # save the cluster the candidate cluster query can consider it.

            updated_clusters.append(selected_cluster)

        db.session.commit()
        return updated_clusters
