from os import environ

from argos.conf import APP

from flask import Flask

app = Flask(__name__,
            static_folder='static',
            static_url_path='')

app.config.update(APP)

if environ.get('FLASK_ENV') == 'TESTING':
    app.config['SQLALCHEMY_DATABASE_URI'] = 'postgresql://argos_user:password@localhost:5432/argos_test'
