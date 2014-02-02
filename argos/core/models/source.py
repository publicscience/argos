from argos.datastore import db, Model

class Source(Model):
    """
    A feed source.
    """
    id = db.Column(db.Integer, primary_key=True)
    url = db.Column(db.Unicode)
    errors = db.Column(db.Integer, default=0)
    articles = db.relationship('Article', backref='source', lazy='dynamic')

    def __init__(self, url):
        self.url = url
