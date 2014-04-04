from argos import web
from argos.web.front.social import oauth
from argos.web.front.assets import assets

def create_app(**config_overrides):
    app = web.create_app(__name__, __path__, **config_overrides)

    oauth.init_app(app)
    assets.init_app(app)

    # So we can use Jade templates.
    app.jinja_env.add_extension('pyjade.ext.jinja.PyJadeExtension')

    return app
