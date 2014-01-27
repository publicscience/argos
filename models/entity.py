from app import db
from slugify import slugify

class Entity(db.Model):
    """
    An entity,
    which could be a place, person,
    organization, concept, topic, etc.
    """
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.UnicodeText)
    slug = db.Column(db.String(255))

    def __init__(self, name):
        self.name = name
        self.slug = slugify(self.name)
