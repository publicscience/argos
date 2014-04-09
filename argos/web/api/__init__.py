from argos import web
from argos.web.api.oauth import oauth

from flask.ext.restful import Api

import os

api = Api()

def create_app(**config_overrides):
    app = web.create_app(__name__, __path__, **config_overrides)

    tmpl_dir = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'templates')
    app.template_folder = tmpl_dir

    api.init_app(app)
    oauth.init_app(app)

    return app
