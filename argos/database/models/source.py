from database.datastore import db

class Source(db.Model):
    """
    A feed source.
    """
    id = db.Column(db.Integer, primary_key=True)
    url = db.Column(db.Unicode)
    errors = db.Column(db.Integer, default=0)
    articles = db.relationship('Article', backref='source', lazy='dynamic')
