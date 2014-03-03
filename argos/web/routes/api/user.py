import argos.web.models as models

from argos.datastore import db
from argos.web.routes.api import api, not_found, unauthorized, page_parser, DateTimeField, STORY_FIELDS

from flask import request
from flask_security.core import current_user
from flask.ext.restful import Resource, marshal_with, fields, reqparse

parser = reqparse.RequestParser()

# temporary, expected to be replaced with mutable user settings.
parser.add_argument('something', type=str)

watching_parser = reqparse.RequestParser()
watching_parser.add_argument('story_id', type=int)

permitted_user_fields = {
    'id': fields.Integer,
    'image': fields.String,
    'name': fields.String,
    'updated_at': DateTimeField,
    'created_at': DateTimeField
}

class CurrentUser(Resource):
    @marshal_with(permitted_user_fields)
    def get(self):
        if current_user.is_authenticated():
            return current_user
        else:
            return unauthorized()

    @marshal_with(permitted_user_fields)
    def patch(self):
        if current_user.is_authenticated():
            for key, val in parser.parse_args().items():
                setattr(current_user, key, val)
            db.session.commit()
            return current_user
        else:
            return unauthorized()
api.add_resource(CurrentUser, '/user')

class CurrentUserWatching(Resource):
    @marshal_with(STORY_FIELDS)
    def get(self):
        if current_user.is_authenticated():
            return current_user.watching
        else:
            return unauthorized()
    @marshal_with(STORY_FIELDS)
    def post(self):
        if current_user.is_authenticated():
            id = watching_parser.parse_args()['story_id']
            story = models.Story.query.get(id)
            if not story:
                return not_found()
            current_user.watching.append(story)
            db.session.commit()
            return story
        else:
            return unauthorized()
api.add_resource(CurrentUserWatching, '/user/watching')

class User(Resource):
    @marshal_with(permitted_user_fields)
    def get(self, id):
        result = models.User.query.get(id)
        return result or not_found()
api.add_resource(User, '/users/<int:id>')

class Users(Resource):
    def get(self):
        args = page_parser.parse_args()
        results = models.User.query.paginate(args['page']).items
        return results or not_found()
api.add_resource(Users, '/users')


