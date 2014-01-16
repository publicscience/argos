from os import environ
from flask import Flask
from flask.ext.sqlalchemy import SQLAlchemy

app = Flask(__name__, static_folder='static', static_url_path='')
app.config.from_object('config')

if environ.get('FLASK_ENV') == 'TESTING':
    app.config['SQLALCHEMY_DATABASE_URI'] = 'postgresql://localhost:5432/argos_test'

db = SQLAlchemy(app)

from app import routes
