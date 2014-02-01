from flask.ext.sqlalchemy import SQLAlchemy
from flask.ext.security import SQLAlchemyUserDatastore, Security

db = SQLAlchemy()

def init_with_flask(app):
    """ 
    Initialize the database with a 
    Flask application.
    """
    import database.models as models

    # Create object for Flask-Security
    user_db = SQLAlchemyUserDatastore(db, models.User, models.Role)
    Security(app, user_db)

    db.init_app(app)
    db.app = app

    db.create_all()
