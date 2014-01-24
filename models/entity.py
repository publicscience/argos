from app import db

class Entity(db.Model):
    """
    An entity,
    which could be a place, person,
    organization, concept, topic, etc.
    """
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.UnicodeText)

    def __init__(self, name):
        self.name = name
