from app import db
from models.entity import Entity
from models.cluster import Clusterable
from brain import vectorize, entities
from scipy.spatial.distance import jaccard

# Helper table for many-to-many.
authors = db.Table('authors',
        db.Column('author_id', db.Integer, db.ForeignKey('author.id')),
        db.Column('article_id', db.Integer, db.ForeignKey('article.id'))
)

article_entities = db.Table('article_entities',
        db.Column('entity_id', db.Integer, db.ForeignKey('entity.id')),
        db.Column('article_id', db.Integer, db.ForeignKey('article.id'))
)

class Article(Clusterable):
    """
    An article.
    """
    __tablename__ = 'article'
    id = db.Column(db.Integer, db.ForeignKey('clusterable.id'), primary_key=True)
    vectors = db.Column(db.PickleType)
    title = db.Column(db.Unicode)
    text = db.Column(db.UnicodeText)
    html = db.Column(db.UnicodeText)
    url = db.Column(db.Unicode)
    published = db.Column(db.DateTime)
    updated = db.Column(db.DateTime)
    source_id = db.Column(db.Integer, db.ForeignKey('source.id'))
    entities = db.relationship('Entity', secondary=article_entities, backref=db.backref('articles', lazy='dynamic'))
    authors = db.relationship('Author', secondary=authors, backref=db.backref('articles', lazy='dynamic'))
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
            # Need to find a way of getting canonical name.
            e = Entity.query.filter_by(name=e_name).first()
            if not e:
                e = Entity(e_name)
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
            s = 1 - jaccard(v_[i], v[i])
            sim += (coefs[i] * s)

        # Normalize back to [0, 1].
        return sim/sum(coefs)
