from argos.datastore import db
from argos.core.models.concept import Concept, Alias, BaseConceptAssociation
from argos.core.models.cluster import Clusterable
from argos.core import brain
from argos.core import knowledge

from scipy.spatial.distance import jaccard
from sqlalchemy import event
from slugify import slugify

from math import isnan
from collections import Counter
from datetime import datetime

# Ignore the invalid numpy warning,
# which comes up when jaccard uses
# empty vectors.
import numpy
numpy.seterr(invalid='ignore')

articles_authors = db.Table('authors',
        db.Column('author_id', db.Integer, db.ForeignKey('author.id')),
        db.Column('article_id', db.Integer, db.ForeignKey('article.id'))
)

articles_mentions = db.Table('articles_mentions',
        db.Column('alias_id', db.Integer, db.ForeignKey('alias.id')),
        db.Column('article_id', db.Integer, db.ForeignKey('article.id'))
)

class ArticleConceptAssociation(BaseConceptAssociation):
    __backref__ = 'article_associations'
    article_id  = db.Column(db.Integer, db.ForeignKey('article.id'), primary_key=True)

class Article(Clusterable):
    """
    An article.
    """
    __tablename__   = 'article'
    __concepts__    = {'association_model': ArticleConceptAssociation, 'backref_name': 'article'}
    __mentions__    = {'secondary': articles_mentions, 'backref_name': 'articles'}
    title       = db.Column(db.Unicode)
    text        = db.Column(db.UnicodeText)
    html        = db.Column(db.UnicodeText)
    ext_url     = db.Column(db.Unicode)
    image       = db.Column(db.String)
    score       = db.Column(db.Float, default=0.0)
    source_id   = db.Column(db.Integer, db.ForeignKey('source.id'))
    feed_id     = db.Column(db.Integer, db.ForeignKey('feed.id'))
    authors     = db.relationship('Author',
                    secondary=articles_authors,
                    backref=db.backref('articles', lazy='dynamic'))

    def __init__(self, **kwargs):
        for key in kwargs:
            setattr(self, key, kwargs[key])

        if self.text is not None:
            self.conceptize()
            self.vectorize()

        if self.score is None:
            self.score = 0.0

    def vectorize(self):
        """
        Returns a tuple of vectors representing this article.

        Articles are represented by:
            (bag of words vector, concepts vector)
        """
        if not hasattr(self, 'vectors') or self.vectors is None:
            bow_vec = brain.vectorize(self.text)
            ent_vec = brain.vectorize(' '.join([c.slug for c in self.concepts]))
            self.vectors = [bow_vec, ent_vec]
        return self.vectors

    def conceptize(self):
        """
        Process the article text for concepts,
        and add the appropriate mentions.
        """
        concepts = []
        for c_name in brain.concepts(self.text):
            # Search for the concept.
            uri = knowledge.uri_for_name(c_name)

            if uri:
                slug = uri.split('/')[-1]
            else:
                slug = slugify(c_name)
            c = Concept.query.get(slug)

            # If an concept is found...
            if c:
                # Add this name as a new alias, if necessary.
                alias = Alias.query.filter_by(name=c_name, concept=c).first()
                if not alias:
                    alias = Alias(c_name)
                    c.aliases.append(alias)
                self.mentions.append(alias)

            # If one doesn't exist, create a new one.
            if not c:
                c = Concept(c_name)
                self.mentions.append(c.aliases[0])
                db.session.add(c)
                db.session.commit()

            concepts.append(c)

        # Score the concepts' importance.
        total_found = len(concepts)
        counter = Counter(concepts)
        uniq_concepts = set(concepts)

        assocs = []
        for concept in uniq_concepts:
            score = counter[concept]/total_found
            assoc = ArticleConceptAssociation(concept, score)
            assocs.append(assoc)

        self.concept_associations = assocs

    def similarity(self, article):
        """
        Calculate the similarity between this article
        and another article.
        """
        # Compare the text vectors,
        # and the concept vectors.
        v = self.vectorize()
        v_ = article.vectorize()

        # Linearly combine the similarity values,
        # weighing them according to these coefficicepts.
        # [text vector, concept vector, publication date]
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

@event.listens_for(Article, 'before_update')
def receive_before_update(mapper, connection, target):
    target.updated_at = datetime.utcnow()
