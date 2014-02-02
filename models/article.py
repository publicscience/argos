from app import db
from models.entity import Entity
from models.cluster import Clusterable
from brain import vectorize, entities
from scipy.spatial.distance import jaccard
from math import isnan
from slugify import slugify

# Ignore the invalid numpy warning,
# which comes up when jaccard uses
# empty vectors.
import numpy
numpy.seterr(invalid='ignore')

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
    image       = db.Column(db.String())
    source_id   = db.Column(db.Integer, db.ForeignKey('source.id'))
    entities    = db.relationship('Entity',
                    secondary=article_entities,
                    backref=db.backref('articles', lazy='dynamic'))
    authors     = db.relationship('Author',
                    secondary=authors,
                    backref=db.backref('articles', lazy='dynamic'))
    __mapper_args__ = {'polymorphic_identity': 'article'}

    def __init__(self, **kwargs):
        for key in kwargs:
            setattr(self, key, kwargs[key])

        if self.text is not None:
            self.entitize()
            self.vectorize()

    def vectorize(self):
        """
        Returns a tuple of vectors representing this article.

        Articles are represented by:
            (bag of words vector, entities vector)
        """
        if self.vectors is None:
            bow_vec = vectorize(self.text)
            ent_vec = vectorize(' '.join(entities(self.text)))
            self.vectors = [bow_vec, ent_vec]
        return self.vectors

    def entitize(self):
        """
        Process the article text for entities.
        """
        ents = []
        for e_name in entities(self.text):
            # TO DO: Need to find a way of getting canonical name.

            # Search for the entity.
            slug = slugify(e_name)
            e = Entity.query.get(slug)

            # If one doesn't exist, create a new one.
            if not e:
                e = Entity(e_name)
                db.session.add(e)
                db.session.commit()
            ents.append(e)
        self.entities = ents

    def similarity(self, article):
        """
        Calculate the similarity between this article
        and another article.
        """
        v = self.vectorize()
        v_ = article.vectorize()

        # Linearly combine the similarity values,
        # weighing them according to these coefficients.
        coefs = [2, 1]
        sim = 0
        for i, vec in enumerate(v):
            dist = jaccard(v_[i], v[i])

            # Two empty vectors returns a jaccard distance of NaN.
            # Set it to be 1, i.e. consider them completely different
            # (or, put more clearly, they have nothing in common)
            # FYI if jaccard runs on empty vectors, it will throw a warning.
            if isnan(dist):
                dist = 1
            s = 1 - dist
            sim += (coefs[i] * s)

        # Normalize back to [0, 1].
        return sim/sum(coefs)
