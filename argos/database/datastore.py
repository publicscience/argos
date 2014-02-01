from flask.ext.sqlalchemy import SQLAlchemy
from flask.ext.security import SQLAlchemyUserDatastore, Security

"""
An `init_db` function should be called to 
initialize this value to be used.
"""
db = None

def init_db_flask(app):
    """ 
    Initialize the database with a 
    Flask application.
    """
    global db 
    
    db = SQLAlchemy(app)

    import database.models as models

    # Create object for Flask-Security
    user_db = SQLAlchemyUserDatastore(db, models.User, models.Role)
    Security(app, user_db)

    db.create_all()

def init_db():
    """
    Initialize a database
    """
    pass
