from argos.web.app import app
from argos.datastore import init_db, init_model

from flask.ext.sqlalchemy import SQLAlchemy
from flask.ext.security import SQLAlchemyUserDatastore, Security

# Initialize the database and declarative Base class
db = SQLAlchemy(app)

init_db(db)

init_model(db.Model)

# Setup security
import argos.web.models

user_db = SQLAlchemyUserDatastore(db, web.models.User, web.models.Role)
Security(app, user_db)

db.create_all()

# Import routes (which depend on database)
from argos.web import routes
