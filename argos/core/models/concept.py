from argos.datastore import db, Model

from argos.core import brain
from argos.core.brain import knowledge

from slugify import slugify
from datetime import datetime
from sqlalchemy import event

concepts_concepts = db.Table('concepts_concepts',
        db.Column('from_concept_slug', db.String, db.ForeignKey('concept.slug')),
        db.Column('to_concept_slug', db.String, db.ForeignKey('concept.slug'))
)

concepts_mentions = db.Table('concepts_mentions',
        db.Column('alias_id', db.Integer, db.ForeignKey('alias.id')),
        db.Column('concept_slug', db.String, db.ForeignKey('concept.slug'))
)

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
    to_concepts = db.relationship('Concept',
                            secondary=concepts_concepts,
                            primaryjoin=slug==concepts_concepts.c.from_concept_slug,
                            secondaryjoin=slug==concepts_concepts.c.to_concept_slug,
                            backref='from_concepts')
    mentions    = db.relationship('Alias', secondary=concepts_mentions, backref=db.backref('concepts'))

    def __init__(self, name):
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
        self.image = k['image']
        self.name = k['name']

        # If there's a summary,
        # extract concepts from it.
        if self.summary:
            self.conceptize()

    @property
    def names(self):
        return [alias.name for alias in self.aliases]

    @property
    def related_concepts(self):
        return self.to_concepts + self.from_concepts

    def conceptize(self):
        """
        Process the concept summary for concepts,
        and add the appropriate mentions.

        For now, this does nothing because the concepts'
        summaries are parsed for concepts, which then can
        lead to the creation of new concepts, which means
        the parsing of those concepts' summaries, ad nauseam...

        Need to come up with a good strategy for dealing with this.
        """
        pass

@event.listens_for(Concept, 'before_update')
def receive_before_update(mapper, connection, target):
    target.updated_at = datetime.utcnow()
