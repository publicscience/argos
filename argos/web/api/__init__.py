from argos import web
from argos.web.api.oauth import oauth

from flask.ext.restful import Api

api = Api()

def create_app(**config_overrides):
    app = web.create_app(__name__, __path__, **config_overrides)

    api.init_app(app)
    oauth.init_app(app)

    return app
