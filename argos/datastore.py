"""
The `init_db` function should be called to
initialize this value to be used.
"""
db = None

"""
The `init_model` function should be called to
initialize this value to be used.
"""
Model = None

def init_db(_db):
    """
    Initialize a database
    """
    global db

    db = _db

    return db

def init_model(_Model):
    """
    Initialize the declarative Base
    """
    global Model

    Model = _Model

    return Model
