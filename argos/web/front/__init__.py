from argos import web
from argos.web.front.social import oauth
from argos.web.front.assets import assets

from flask.ext.babel import Babel

import os

def create_app(**config_overrides):
    app = web.create_app(__name__, __path__, **config_overrides)

    tmpl_dir = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'templates')
    static_dir = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'static')
    app.template_folder = tmpl_dir
    app.static_folder = static_dir

    oauth.init_app(app)
    assets.init_app(app)
    babel = Babel(app)

    # So we can use Jade templates.
    app.jinja_env.add_extension('pyjade.ext.jinja.PyJadeExtension')

    return app
