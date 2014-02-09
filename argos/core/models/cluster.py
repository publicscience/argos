from argos.datastore import db, Model
from argos.core.brain import vectorize, entities
from argos.core.brain.summarize import summarize, multisummarize

from sqlalchemy.ext.declarative import declared_attr
from scipy.spatial.distance import jaccard

from datetime import datetime
from itertools import chain


class Clusterable(Model):
    """
    An abstract class for anything that can be clustered.
    """
    __abstract__ = True
    id          = db.Column(db.Integer, primary_key=True)
    created_at  = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at  = db.Column(db.DateTime, default=datetime.utcnow)

    @declared_attr
    def entities(cls):
        """
        Build the entities attribute from the
        subclass's `__entities__` class attribute.

        Example::

            __entities__ = {'secondary': articles_entities, 'backref_name': 'articles'}
        """
        args = cls.__entities__

        return db.relationship('Entity',
                secondary=args['secondary'],
                backref=db.backref(args['backref_name']))

    def vectorize(self):
        raise NotImplementedError

    def similarity(self):
        raise NotImplementedError


class Cluster(Clusterable):
    """
    A cluster.

    A Cluster is capable of clustering Clusterables.

    Note: A Cluster itself is a Clusterable; i.e. clusters
    can cluster clusters :)
    """
    __abstract__ = True
    title       = db.Column(db.Unicode)
    summary     = db.Column(db.UnicodeText)
    image       = db.Column(db.String())

    @declared_attr
    def members(cls):
        """
        Build the members attribute from the
        subclass's `__members__` class attribute.

        Example::

            __members__ = {'class_name': 'Article', 'secondary': events_articles, 'backref_name': 'events'}
        """
        args = cls.__members__

        return db.relationship(args['class_name'],
                secondary=args['secondary'],
                backref=db.backref(args['backref_name']))

    @staticmethod
    def cluster(cls, clusterables):
        """
        The particular clustering method for this Cluster class.
        Must be implemented on subclasses, otherwise raises NotImplementedError.
        """
        raise NotImplementedError

    def __init__(self, members):
        """
        Initialize a cluster with some members and a tag.

        Tags are used to keep track of "levels" or "kinds" of clusters.
        """
        self.members = members
        self.update()

    def summarize(self):
        """
        Generate a summary for this cluster.
        """
        if len(self.members) == 1:
            member = self.members[0]
            self.summary = ' '.join(summarize(member.title, member.text))
        else:
            self.summary = ' '.join(multisummarize([m.text for m in self.members]))
        return self.summary

    def titleize(self):
        """
        Generate a title for this cluster.

        Looks for the cluster member that is most similar to the others,
        and then uses the title of that member.
        """
        max_member = (None, 0)
        for member in self.members:
            avg_sim = self.similarity(member)
            if avg_sim >= max_member[1]:
                max_member = (member, avg_sim)
        self.title = max_member[0].title
        self.image = max_member[0].image

    def entitize(self):
        """
        Update entities for this cluster.
        """
        self.entities = list(set(chain.from_iterable([member.entities for member in self.members])))

    def update(self):
        """
        Update the cluster's attributes,
        optionally saving (saves by default).
        """
        self.titleize()
        self.summarize()
        self.entitize()
        self.updated_at = datetime.utcnow()
        self.created_at = datetime.utcnow()

    def add(self, member):
        """
        Add an member to the cluster.
        """
        self.members.append(member)

    def similarity(self, obj):
        """
        Calculate the similarity of an object with this cluster,
        or the similarity between another cluster and this cluster.
        If it is an object, that object must have a `similarity` method implemented.
        """
        sims = [obj.similarity(member) for member in self.members]

        # Calculate average similarity.
        return sum(sims)/len(sims)

    def timespan(self, start, end=None):
        """
        Get cluster members within a certain (date)timespan.

        Args:
            | start (datetime)
            | end (datetime)    -- default is now (UTC)
        """
        if end is None:
            end = datetime.utcnow()
        return [member for member in self.members if start < member.created_at < end]
