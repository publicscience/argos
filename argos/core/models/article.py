from argos.datastore import db, join_table
from argos.core.models.concept import Concept, Alias, BaseConceptAssociation
from argos.core.models.cluster import Clusterable
from argos.core import brain
from argos.core import knowledge

from sqlalchemy import event
from slugify import slugify

from collections import Counter
from datetime import datetime

# Ignore the invalid numpy warning,
# which comes up when jaccard uses
# empty vectors.
import numpy
numpy.seterr(invalid='ignore')

articles_authors = join_table('articles_authors', 'article', 'author')
articles_mentions = join_table('articles_mentions', 'article', 'alias')

class ArticleConceptAssociation(BaseConceptAssociation):
    __backref__ = 'article_associations'
    article_id  = db.Column(db.Integer, db.ForeignKey('article.id', ondelete='CASCADE', onupdate='CASCADE'), primary_key=True)

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

    def __str__(self):
        return self.title

    def __repr__(self):
        return self.title

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
            bow_vec = brain.vectorizer.vectorize(self.text)
            ent_vec = brain.conceptor.vectorize(' '.join([c.slug for c in self.concepts]))
            self.vectors = [bow_vec, ent_vec]
        return self.vectors

    def conceptize(self):
        """
        Process the article text for concepts,
        and add the appropriate mentions.
        """
        concepts = []
        for c_name in brain.conceptor.concepts(self.text):
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
                # Avoid duplicate aliases.
                if alias not in self.mentions:
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

@event.listens_for(Article, 'before_update')
def receive_before_update(mapper, connection, target):
    target.updated_at = datetime.utcnow()
