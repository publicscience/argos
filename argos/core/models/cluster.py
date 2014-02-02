from argos.datastore import db, Model
from argos.core.brain import vectorize, entities

from scipy.spatial.distance import jaccard

from datetime import datetime
from itertools import chain

cluster_entities = db.Table('cluster_entities',
        db.Column('entity_slug', db.String, db.ForeignKey('entity.slug')),
        db.Column('cluster_id', db.Integer, db.ForeignKey('cluster.id'))
)

cluster_clusterables = db.Table('cluster_clusterables',
        db.Column('cluster_id', db.Integer, db.ForeignKey('cluster.id'), primary_key=True),
        db.Column('clusterable_id', db.Integer, db.ForeignKey('clusterable.id'), primary_key=True)
)

class Clusterable(Model):
    id          = db.Column(db.Integer, primary_key=True)
    type        = db.Column('type', db.String(50))
    created_at  = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at  = db.Column(db.DateTime, default=datetime.utcnow)
    __mapper_args__ = {'polymorphic_on': 'type'}

    def vectorize(self):
        raise Exception('Not implemented!')

    def similarity(self):
        raise Exception('Not implemented!')

class Cluster(Clusterable):
    """
    A cluster.

    A Cluster is capable of clustering Clusterables.

    Note: A Cluster itself is a Clusterable; i.e. clusters
    can cluster clusters :)
    """
    __tablename__ = 'cluster'
    id          = db.Column(db.Integer, db.ForeignKey('clusterable.id'), primary_key=True)
    active      = db.Column(db.Boolean, default=True)
    title       = db.Column(db.Unicode)
    summary     = db.Column(db.UnicodeText)
    tag         = db.Column(db.String(50))
    entities    = db.relationship('Entity',
                    secondary=cluster_entities,
                    backref=db.backref('clusters', lazy='dynamic'))
    members     = db.relationship('Clusterable',
                    secondary=cluster_clusterables,
                    backref=db.backref('clusters'))

    __mapper_args__ = {
            'polymorphic_identity': 'cluster',
            'inherit_condition': (id == Clusterable.id)
    }

    def __init__(self, members, tag=''):
        """
        Initialize a cluster with some members and a tag.

        Tags are used to keep track of "levels" or "kinds" of clusters.
        """
        self.members = members
        self.tag = tag
        self.update()

    def summarize(self):
        """
        Generate a summary for this cluster.
        """
        # something like:
        # self.summary = summarize([m.text for m in self.members])
        pass

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


    # May not be necessary.
    def similarity_with_cluster(self, cluster):
        """
        Calculate the average similarity of each
        member to each member of the other cluster.
        """
        avg_sims = []
        vs = self.vectorize()
        vs_ = cluster.vectorize()
        return 1 - jaccard(vs, vs_)

    # May not be necessary.
    def vectorize(self):
        """
        Vectorize all members in a cluster
        into a 1D array.
        """
        return vectorize([m.text for m in self.members]).toarray().flatten()
