from argos.datastore import db, Model
from argos.core.models.entity import Entity, Alias
from argos.core.models.cluster import Clusterable
from argos.core.brain import vectorize, entities, knowledge

from scipy.spatial.distance import jaccard

from math import isnan
from slugify import slugify

# Ignore the invalid numpy warning,
# which comes up when jaccard uses
# empty vectors.
import numpy
numpy.seterr(invalid='ignore')

articles_authors = db.Table('authors',
        db.Column('author_id', db.Integer, db.ForeignKey('author.id')),
        db.Column('article_id', db.Integer, db.ForeignKey('article.id'))
)

articles_entities = db.Table('articles_entities',
        db.Column('entity_slug', db.String, db.ForeignKey('entity.slug')),
        db.Column('article_id', db.Integer, db.ForeignKey('article.id'))
)

class Article(Clusterable):
    """
    An article.
    """
    __tablename__ = 'article'
    __entities__    = {'secondary': articles_entities, 'backref_name': 'articles'}
    vectors     = db.Column(db.PickleType)
    title       = db.Column(db.Unicode)
    text        = db.Column(db.UnicodeText)
    html        = db.Column(db.UnicodeText)
    ext_url     = db.Column(db.Unicode)
    image       = db.Column(db.String)
    score       = db.Column(db.Integer)
    source_id   = db.Column(db.Integer, db.ForeignKey('source.id'))
    authors     = db.relationship('Author',
                    secondary=articles_authors,
                    backref=db.backref('articles', lazy='dynamic'))

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
            # Search for the entity.
            uri = knowledge.uri_for_name(e_name)

            if uri:
                slug = uri.split('/')[-1]
            else:
                slug = slugify(e_name)
            e = Entity.query.get(slug)

            # If an entity is found...
            if e:
                # Add this name as a new alias, if necessary.
                if e_name not in [a.name for a in e.aliases]:
                    e.aliases.append(Alias(name))

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
        # Compare the text vectors,
        # and the entity vectors.
        v = self.vectorize()
        v_ = article.vectorize()

        # Linearly combine the similarity values,
        # weighing them according to these coefficients.
        # [text vector, entity vector, publication date]
        coefs = [2, 1, 2]
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

        # Also take publication dates into account.
        ideal_time = 259200 # 3 days, in seconds
        t, t_ = self.created_at, article.created_at

        # Subtract the more recent time from the earlier time.
        time_diff = t - t_ if t > t_ else t_ - t
        time_diff = time_diff.total_seconds()

        # Score is normalized [0, 1], where 1 is within the ideal time,
        # and approaches 0 the longer the difference is from the ideal time.
        time_score = 1 if time_diff < ideal_time else ideal_time/time_diff
        sim += (coefs[2] * time_score)

        # Normalize back to [0, 1].
        return sim/sum(coefs)
