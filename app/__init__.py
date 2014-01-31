from conf import APP
from os import environ

from flask import Flask
from flask.ext.sqlalchemy import SQLAlchemy
from flask.ext.security import SQLAlchemyUserDatastore, Security

app = Flask(__name__, static_folder='static', static_url_path='')
app.config.update(APP)

if environ.get('FLASK_ENV') == 'TESTING':
    app.config['SQLALCHEMY_DATABASE_URI'] = 'postgresql://localhost:5432/argos_test'

db = SQLAlchemy(app)

from app import routes
import models

user_datastore = SQLAlchemyUserDatastore(db, models.User, models.Role)
security = Security(app, user_datastore)

db.create_all()
