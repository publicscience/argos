from argos.datastore import db, Model

class Source(Model):
    """
    A feed source.
    """
    id = db.Column(db.Integer, primary_key=True)
    ext_url = db.Column(db.Unicode)
    name = db.Column(db.String(255))
    errors = db.Column(db.Integer, default=0)
    articles = db.relationship('Article', backref='source', lazy='dynamic')
