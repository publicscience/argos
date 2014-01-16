from app import db
from brain import vectorize, entities

# Helper table for many-to-many.
authors = db.Table('authors',
        db.Column('author_id', db.Integer, db.ForeignKey('author.id')),
        db.Column('article_id', db.Integer, db.ForeignKey('article.id'))
)

class Article(db.Model):
    """
    An article.
    """
    id = db.Column(db.Integer, primary_key=True)
    vectors = db.Column(db.PickleType)
    title = db.Column(db.Unicode)
    text = db.Column(db.UnicodeText)
    html = db.Column(db.UnicodeText)
    url = db.Column(db.Unicode)
    published = db.Column(db.DateTime)
    updated = db.Column(db.DateTime)
    cluster_id = db.Column(db.Integer, db.ForeignKey('cluster.id'))
    source_id = db.Column(db.Integer, db.ForeignKey('source.id'))
    authors = db.relationship('Author', secondary=authors, backref=db.backref('articles', lazy='dynamic'))

    def __init__(self, **kwargs):
        for key in kwargs:
            setattr(self, key, kwargs[key])

        if self.text is not None:
            self.vectorize()

    def vectorize(self):
        # Articles are represented by:
        # – bag of words vector
        # – entities vector
        if self.vectors is None:
            bow_vec = vectorize(self.text)
            ent_vec = vectorize(' '.join(entities(self.text)))
            self.vectors = [bow_vec, ent_vec]
        return self.vectors

