from argos.conf import APP
from argos.datastore import db

from flask import Flask
from flask.ext.migrate import Migrate

def create_app(package_name=__name__, package_path=__path__, **config_overrides):
    app = Flask(package_name, static_url_path='')
    app.config.update(APP)

    # Apply overrides.
    app.config.update(config_overrides)

    # Initialize the database and declarative Base class.
    db.init_app(app)
    Migrate(app, db)

    # Create the database tables.
    # Flask-SQLAlchemy needs to know which
    # app context to create the tables in.
    with app.app_context():
        db.create_all()

    return app
