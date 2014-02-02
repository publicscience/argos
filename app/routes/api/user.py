from . import api, not_found, unauthorized, page_parser, DateTimeField
from flask_security.core import current_user
from flask.ext.restful import Resource, marshal_with, fields, reqparse
from flask import request
import models

parser = reqparse.RequestParser()
parser.add_argument('something', type=str)

class CurrentUser(Resource):
    @marshal_with({
        'id': fields.Integer,
        'image': fields.String,
        'name': fields.String
    })
    def get(self):
        if current_user.is_authenticated():
            return current_user
        else:
            return unauthorized()
    def patch(self):
        if current_user.is_authenticated():
            for key, val in parser.parse_args().items():
                setattr(current_user, key, val)
            db.session.commit()
            return current_user
        else:
            return unauthorized()
api.add_resource(CurrentUser, '/user')

class User(Resource):
    @marshal_with({
        'id': fields.Integer,
        'image': fields.String,
        'name': fields.String,
        'updated_at': DateTimeField,
        'created_at': DateTimeField
    })
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


