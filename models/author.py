from app import db

class Author(db.Model):
    """
    An author.
    """
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.Unicode)
