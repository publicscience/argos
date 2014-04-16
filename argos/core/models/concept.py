from argos.datastore import db, Model

from argos.core import brain
from argos.core import knowledge
from argos.util import storage

from slugify import slugify
from datetime import datetime
from os.path import splitext
from sqlalchemy import event
from sqlalchemy.ext.declarative import declared_attr

from collections import Counter

concepts_mentions = db.Table('concepts_mentions',
        db.Column('alias_id', db.Integer, db.ForeignKey('alias.id')),
        db.Column('concept_slug', db.String, db.ForeignKey('concept.slug'))
)

class BaseConceptAssociation(Model):
    """
    Models which will be related to concepts must
    subclass this model and specify a backref name
    through a class property called `__backref__`
    and a foreign key property for the related model.

    Example::

        class ArticleConceptAssociation(BaseConceptAssociation):
            __backref__ = 'article_associations'
            article_id  = db.Column(db.Integer, db.ForeignKey('article.id'), primary_key=True)

    In the related model, you must also specify a
    `__concepts__` class property which points to this association
    model:

            __concepts__ = {'association_model': ArticleConceptAssociation,
                            'backref_name': 'article'}
    """
    __abstract__ = True
    score           = db.Column(db.Float, default=0.0)

    def __init__(self, concept, score):
        self.score = score
        self.concept = concept

    @declared_attr
    def concept(cls):
        backref = cls.__backref__
        return db.relationship('Concept', backref=backref)

    @declared_attr
    def concept_slug(cls):
        return db.Column(db.String, db.ForeignKey('concept.slug'), primary_key=True)


class ConceptConceptAssociation(BaseConceptAssociation):
    from_concept_slug   = db.Column(db.String, db.ForeignKey('concept.slug'), primary_key=True)
    concept_slug        = db.Column(db.String, db.ForeignKey('concept.slug'), primary_key=True)
    concept             = db.relationship('Concept', backref=db.backref('from_concept_associations'), foreign_keys=[concept_slug])


class Alias(Model):
    """
    An alias (i.e. a name) for a concept.
    """
    id          = db.Column(db.Integer, primary_key=True)
    name        = db.Column(db.UnicodeText)
    slug        = db.Column(db.String, db.ForeignKey('concept.slug'))

    def __init__(self, name):
        self.name = name


class Concept(Model):
    """
    An concept,
    which could be a place, person,
    organization, topic, etc.

    You should *not* set the `slug` or `uri`;
    they are set automatically according to the `name`.
    In the spirit of Python's developer maturity,
    you're trusted not to modify them.
    """
    name        = db.Column(db.UnicodeText)
    slug        = db.Column(db.String(255), primary_key=True)
    uri         = db.Column(db.String)
    summary     = db.Column(db.UnicodeText)
    image       = db.Column(db.String)
    updated_at  = db.Column(db.DateTime, default=datetime.utcnow)
    created_at  = db.Column(db.DateTime, default=datetime.utcnow)
    aliases     = db.relationship('Alias', backref='concept', lazy='joined')

    # Mapping concepts to concepts,
    # and tracking mentions of other concepts in this concept's summary.
    mentions    = db.relationship('Alias', secondary=concepts_mentions, backref=db.backref('concepts'))
    concept_associations = db.relationship(ConceptConceptAssociation,
                                foreign_keys=[ConceptConceptAssociation.from_concept_slug],
                                backref=db.backref('from_concept'),
                                cascade='all, delete-orphan')

    def __init__(self, name):
        """
        Initialize a concept by a name, which can be
        an alias (it does not have to be the canonical name).
        This specified name will be saved as an Alias.

        A canonical name will be looked for; if one is found
        it will be used as the slug for this Concept.
        """
        self.aliases.append(Alias(name))

        # Try to get a canonical URI
        # and derive the slug from that.
        self.uri = knowledge.uri_for_name(name)
        if self.uri:
            self.slug = self.uri.split('/')[-1]
            k = knowledge.knowledge_for(uri=self.uri, fallback=True)

        # If no URI was found,
        # generate our own slug.
        # Note: A problem here is that it assumes that
        # this particular name is the canonical one.
        else:
            self.slug = slugify(name)
            k = knowledge.knowledge_for(name=name)

        self.summary = k['summary']
        self.name = k['name']

        # Download the image.
        if k['image'] is not None:
            ext = splitext(k['image'])[-1].lower()
            self.image = storage.save_from_url(k['image'], '{0}{1}'.format(hash(self.slug), ext))

    @property
    def names(self):
        return [alias.name for alias in self.aliases]

    @property
    def concepts(self):
        """
        Returns the concepts this
        concept points *to*,
        with their importance scores
        for this concept.
        """
        if self.summary and not len(self.concept_associations):
            self.conceptize()

        def with_score(assoc):
            assoc.concept.score = assoc.score
            return assoc.concept
        return list(map(with_score, self.concept_associations))

    @property
    def from_concepts(self):
        """
        Returns the concepts that
        points to this concept,
        with their importance scores
        for this concept.
        """
        def with_score(assoc):
            assoc.from_concept.score = assoc.score
            return assoc.from_concept
        return list(map(with_score, self.from_concept_associations))

    @property
    def stories(self):
        """
        Return the stories associated with this concept,
        adding an additional "relatedness" value
        which is the concept's importance score for
        a particular story.
        """
        def with_score(assoc):
            assoc.story.relatedness = assoc.score
            return assoc.story
        return list(map(with_score, self.story_associations))

    @property
    def events(self):
        """
        Same as the `stories` property
        but for events.
        """
        def with_score(assoc):
            assoc.event.relatedness = assoc.score
            return assoc.event
        return list(map(with_score, self.event_associations))

    @property
    def articles(self):
        """
        Same as the `stories` property
        but for articles.
        """
        def with_score(assoc):
            assoc.article.relatedness = assoc.score
            return assoc.article
        return list(map(with_score, self.article_associations))

    @property
    def related_concepts(self):
        return self.to_concepts + self.from_concepts

    def conceptize(self):
        """
        Process the concept summary for concepts,
        and add the appropriate mentions.
        """
        concepts = []
        for c_name in brain.concepts(self.summary):
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
            assoc = ConceptConceptAssociation(concept, score)
            assocs.append(assoc)

        self.concept_associations = assocs

@event.listens_for(Concept, 'before_update')
def receive_before_update(mapper, connection, target):
    target.updated_at = datetime.utcnow()
