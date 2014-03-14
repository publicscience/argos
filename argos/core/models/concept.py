from argos.datastore import db, Model

from argos.core.brain import knowledge

from slugify import slugify
from datetime import datetime
from sqlalchemy import event

class Alias(Model):
    """
    An alias (i.e. a name) for a concept.
    """
    id          = db.Column(db.Integer, primary_key=True)
    name        = db.Column(db.UnicodeText)
    slug = db.Column(db.String, db.ForeignKey('concept.slug'))

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

    @property
    def names(self):
        return [alias.name for alias in self.aliases]

@event.listens_for(Concept, 'before_update')
def receive_before_update(mapper, connection, target):
    target.updated_at = datetime.utcnow()
