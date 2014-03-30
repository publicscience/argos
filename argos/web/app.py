from os import environ
import logging
from logging import handlers

from argos.conf import APP

from flask import Flask

app = Flask(__name__,
            static_folder='static',
            static_url_path='')

app.config.update(APP)

if not APP['DEBUG']:
    # Email Flask application exceptions.
    mh = handlers.SMTPHandler(
            (APP['EMAIL_HOST'], APP['EMAIL_PORT']),
            APP['EMAIL_HOST_USER'],
            APP['ADMINS'],
            'Argos Application Error :(',
            credentials=(
                APP['EMAIL_HOST_USER'],
                APP['EMAIL_HOST_PASSWORD']
            ),
            secure=()
    )
    mh.setLevel(logging.ERROR)
    app.logger.addHandler(mh)


if environ.get('FLASK_ENV') == 'TESTING':
    app.config['SQLALCHEMY_DATABASE_URI'] = 'postgresql://argos_user:password@localhost:5432/argos_test'
