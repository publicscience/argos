from argos.datastore import db, Model

from slugify import slugify
from datetime import datetime
from sqlalchemy import event

class Entity(Model):
    """
    An entity,
    which could be a place, person,
    organization, concept, topic, etc.
    """
    name = db.Column(db.UnicodeText)
    slug = db.Column(db.String(255), primary_key=True)
    updated_at  = db.Column(db.DateTime, default=datetime.utcnow)

    def __init__(self, name):
        self.name = name
        self.slug = slugify(self.name)

@event.listens_for(Entity, 'before_update')
def receive_before_update(mapper, connection, target):
    target.slug = slugify(target.name)
    target.updated_at = datetime.utcnow()
