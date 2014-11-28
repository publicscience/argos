from flask.ext.sqlalchemy import SQLAlchemy

db = SQLAlchemy(session_options={'autoflush': False})
Model = db.Model

def join_table(name, a, b):
    """
    Convenience method for building a join table.

    Args:
        | name (str)    -- name to give the table
        | a (str)       -- name of the first table being joined
        | b (str)       -- name of the second table being joined

    Example::

        stories_events = join_table('stories_events', 'story', 'event')
    """
    return db.Table(name,
        db.Column('{0}_id'.format(a),
            db.Integer,
            db.ForeignKey('{0}.id'.format(a), ondelete='CASCADE', onupdate='CASCADE'),
            primary_key=True),

        db.Column('{0}_id'.format(b),
            db.Integer,
            db.ForeignKey('{0}.id'.format(b), ondelete='CASCADE', onupdate='CASCADE'),
            primary_key=True)
)
