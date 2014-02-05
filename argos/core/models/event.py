from argos.datastore import db
from argos.core.models.cluster import Cluster
from argos.core.brain.cluster import cluster

from argos.util.logger import logger

from datetime import datetime

events_articles = db.Table('events_articles',
        db.Column('event_id', db.Integer, db.ForeignKey('event.id'), primary_key=True),
        db.Column('article_id', db.Integer, db.ForeignKey('article.id'), primary_key=True)
)

events_entities = db.Table('events_entities',
        db.Column('entity_slug', db.String, db.ForeignKey('entity.slug')),
        db.Column('event_id', db.Integer, db.ForeignKey('event.id'))
)

class Event(Cluster):
    __tablename__   = 'event'
    __members__     = {'class_name': 'Article', 'secondary': events_articles, 'backref_name': 'events'}
    __entities__    = {'secondary': events_entities, 'backref_name': 'events'}
    active          = db.Column(db.Boolean, default=True)

    @property
    def articles(self):
        """
        Convenience :)
        """
        return self.members

    @articles.setter
    def articles(self, value):
        self.members = value

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
            # i.e. active clusters which share at least one entity with this article.
            a_ents = [entity.slug for entity in article.entities]
            candidate_clusters = []
            for c in active_clusters:
                c_ents = [entity.slug for entity in c.entities]
                if set(c_ents).intersection(a_ents):
                    candidate_clusters.append(c)

            selected_cluster = cluster(article, candidate_clusters, threshold=threshold, logger=log)

            # If no selected cluster was found, then create a new one.
            if not selected_cluster:
                log.debug('No qualifying clusters found, creating a new cluster.')
                selected_cluster = Event([article])
                db.session.add(selected_cluster)

            updated_clusters.append(selected_cluster)

        for clus in active_clusters:
            # Mark expired clusters inactive.
            if (now - clus.updated_at).days > 3:
                clus.active = False
            else:
                clus.update()

        db.session.commit()
        return updated_clusters

