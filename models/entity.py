from app import db
from slugify import slugify

class Entity(db.Model):
    """
    An entity,
    which could be a place, person,
    organization, concept, topic, etc.
    """
    name = db.Column(db.UnicodeText)
    slug = db.Column(db.String(255), primary_key=True)

    def __init__(self, name):
        self.name = name
        self.slug = slugify(self.name)
