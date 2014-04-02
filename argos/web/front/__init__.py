from argos import web
from argos.web.front.social import oauth

def create_app(**config_overrides):
    app = web.create_app(__name__, __path__, **config_overrides)

    oauth.init_app(app)

    return app
