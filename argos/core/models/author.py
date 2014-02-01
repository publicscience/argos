from database.datastore import db, Model

class Author(Model):
    """
    An author.
    """
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.Unicode)

    def __init__(self, name):
        self.name = name

    @classmethod
    def find_or_create(cls, **kwargs):
        obj = cls.query.filter_by(**kwargs).first()
        if obj is None:
            obj = cls(**kwargs)
            db.session.add(obj)
            db.session.commit()
        return obj
