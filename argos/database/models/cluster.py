from datetime import datetime

from database.datastore import db 

cluster_entities = db.Table('cluster_entities',
        db.Column('entity_slug', db.String, db.ForeignKey('entity.slug')),
        db.Column('cluster_id', db.Integer, db.ForeignKey('cluster.id'))
)

cluster_clusterables = db.Table('cluster_clusterables',
        db.Column('cluster_id', db.Integer, db.ForeignKey('cluster.id'), primary_key=True),
        db.Column('clusterable_id', db.Integer, db.ForeignKey('clusterable.id'), primary_key=True)
)

class Clusterable(db.Model):
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
