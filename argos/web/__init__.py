from argos.conf import APP
from argos.datastore import db

from flask import Flask
from flask.ext.security import SQLAlchemyUserDatastore, Security
from flask.ext.migrate import Migrate

from flask import Blueprint
import pkgutil
import importlib

def create_app(package_name=__name__, package_path=__path__, has_blueprints=True, **config_overrides):
    app = Flask(package_name, static_url_path='')
    app.config.update(APP)

    # Apply overrides.
    app.config.update(config_overrides)

    # Initialize the database and declarative Base class.
    db.init_app(app)
    Migrate(app, db)

    # Setup security.
    from argos.web import models
    user_db = SQLAlchemyUserDatastore(db, models.User, models.Role)
    Security(app, user_db)

    # Create the database tables.
    # Flask-SQLAlchemy needs to know which
    # app context to create the tables in.
    with app.app_context():
        db.create_all()

    # Register blueprints.
    if has_blueprints:
        register_blueprints(app, package_name, package_path)

    return app

def register_blueprints(app, package_name, package_path):
    """
    Register all Blueprint instances on the
    specified Flask application found
    in all modules for the specified package.
    """
    results = []
    for _, name, _ in pkgutil.iter_modules(package_path):
        m = importlib.import_module('%s.%s' % (package_name, name))
        for item in dir(m):
            item = getattr(m, item)
            if isinstance(item, Blueprint):
                app.register_blueprint(item)
            results.append(item)
    return results
