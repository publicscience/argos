from database.datastore import db

from database.models.entity import Entity
from database.models.cluster import Clusterable

# Helper table for many-to-many.
authors = db.Table('authors',
        db.Column('author_id', db.Integer, db.ForeignKey('author.id')),
        db.Column('article_id', db.Integer, db.ForeignKey('article.id'))
)

article_entities = db.Table('article_entities',
        db.Column('entity_slug', db.String, db.ForeignKey('entity.slug')),
        db.Column('article_id', db.Integer, db.ForeignKey('article.id'))
)

class Article(Clusterable):
    """
    An article.
    """
    __tablename__ = 'article'
    id          = db.Column(db.Integer, db.ForeignKey('clusterable.id'), primary_key=True)
    vectors     = db.Column(db.PickleType)
    title       = db.Column(db.Unicode)
    text        = db.Column(db.UnicodeText)
    html        = db.Column(db.UnicodeText)
    url         = db.Column(db.Unicode)
    source_id   = db.Column(db.Integer, db.ForeignKey('source.id'))
    entities    = db.relationship('Entity',
                    secondary=article_entities,
                    backref=db.backref('articles', lazy='dynamic'))
    authors     = db.relationship('Author',
                    secondary=authors,
                    backref=db.backref('articles', lazy='dynamic'))
    __mapper_args__ = {'polymorphic_identity': 'article'}
