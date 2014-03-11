from argos.web.app import app
from flask.ext.restful import Api

api = Api(app)

from argos.web.routes import user, search, resources, auth, oauth
