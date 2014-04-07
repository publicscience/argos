from argos.datastore import db, Model

from datetime import datetime

class Source(Model):
    """
    An article source.
    """
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(255), unique=True)
    icon = db.Column(db.String(255))

    # Keep articles on the Source so if an
    # article's feed dies, we still know where the Article came from.
    articles = db.relationship('Article', backref='source', lazy='dynamic')
    feeds = db.relationship('Feed', backref='source', lazy='dynamic')

class Feed(Model):
    """
    A particular feed for a source,
    from which articles can be collected.
    """
    id = db.Column(db.Integer, primary_key=True)
    ext_url = db.Column(db.Unicode, unique=True)
    errors = db.Column(db.Integer, default=0)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow)
    updating = db.Column(db.Boolean, default=False)
    articles = db.relationship('Article', backref='feed', lazy='dynamic')
    source_id   = db.Column(db.Integer, db.ForeignKey('source.id'))
