from argos.datastore import db, Model

from datetime import datetime

class Source(Model):
    """
    A feed source.
    """
    id = db.Column(db.Integer, primary_key=True)
    ext_url = db.Column(db.Unicode)
    name = db.Column(db.String(255))
    errors = db.Column(db.Integer, default=0)
    articles = db.relationship('Article', backref='source', lazy='dynamic')
    updated_at = db.Column(db.DateTime, default=datetime.utcnow)
    updating = db.Column(db.Boolean, default=False)
