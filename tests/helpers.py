from argos.datastore import db

def save(objs=None):
    """
    Saves a set of objects to the database,
    or just saves changes to the database.
    """
    if objs is not None:
        if type(objs) is list:
            db.session.add_all(objs)
        else:
            db.session.add(objs)
    db.session.commit()
