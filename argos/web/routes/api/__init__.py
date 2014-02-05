import argos.web.models as models

from argos.datastore import db
from argos.web.app import app

from flask import request
from flask_security.core import current_user
from flask.ext.restful import Api, Resource, abort, marshal_with, fields, reqparse

api = Api(app)

# Whitelist of allowed request parameters.
page_parser = reqparse.RequestParser()
page_parser.add_argument('page', type=int, default=1)


def not_found():
    return abort(404, message='The resource you requested, {0}, was not found.'.format(request.path), status=404)

def unauthorized():
    return abort(401, message='You are not authorized to access {0}. Have you authenticated?'.format(request.path), status=401)


class DateTimeField(fields.Raw):
    """
    Custom DateTime field, to return
    ISO 8601 formatted datetimes.
    (By default, Flask-Restful uses RFC822)
    """
    def format(self, value):
        return value.isoformat()


def cluster_fields(members={}, custom={}):
    """
    The default fields for any Cluster-like resource.
    """
    fields_ = {
        'id': fields.Integer,
        'title': fields.String,
        'summary': fields.String,
        'updated_at': DateTimeField,
        'created_at': DateTimeField,
        'entities': fields.Nested({
            'name': fields.String,
            'url': fields.Url('entity')
        })
    }

    if members is not None:
        members_ = {
            'title': fields.String,
            'url': fields.String,
            'id': fields.Integer,
            'created_at': DateTimeField
        }
        members_.update(members)

        fields_['members'] = fields.Nested(members_)

    fields_.update(custom)
    return fields_


class Event(Resource):
    @marshal_with(cluster_fields())
    def get(self, id):
        result = models.Event.query.get(id)
        return result or not_found()
class Events(Resource):
    # Doesn't need to return members, i.e. individual articles.
    # That slows it down by a lot, and they aren't necessary here.
    @marshal_with(cluster_fields(members=None))
    def get(self):
        args = page_parser.parse_args()
        results = models.Event.query.paginate(args['page']).items
        return results or not_found()
api.add_resource(Event, '/events/<int:id>')
api.add_resource(Events, '/events')


class Story(Resource):
    @marshal_with(cluster_fields(members={'url': fields.Url('event')}))
    def get(self, id):
        result = models.Story.query.get(id)
        return result or not_found()
class Stories(Resource):
    @marshal_with(cluster_fields(members={'url': fields.Url('event')}))
    def get(self):
        args = page_parser.parse_args()
        results = models.Story.query.paginate(args['page']).items
        return results or not_found()
class StoryWatchers(Resource):
    from argos.web.routes.api.user import permitted_user_fields
    @marshal_with({ 'watchers': fields.Nested(permitted_user_fields) })
    def get(self, id):
        result = models.Story.query.get(id)
        return result or not_found()
    @marshal_with(permitted_user_fields)
    def post(self, id):
        if current_user.is_authenticated():
            result = models.Story.query.get(id)
            result.watchers.append(current_user)
            db.session.commit()
            return current_user
        else:
            return unauthorized()
    @marshal_with(permitted_user_fields)
    def delete(self, id):
        if current_user.is_authenticated():
            result = models.Story.query.get(id)
            result.watchers.remove(current_user)
            db.session.commit()
            return current_user
        else:
            return unauthorized()
api.add_resource(Story, '/stories/<int:id>')
api.add_resource(Stories, '/stories')
api.add_resource(StoryWatchers, '/stories/<int:id>/watchers')


class Entity(Resource):
    @marshal_with({
        'name': fields.String,
        'slug': fields.String
    })
    def get(self, slug):
        result = models.Entity.query.get(slug)
        return result or not_found()
api.add_resource(Entity, '/entities/<string:slug>')

from argos.web.routes.api import user
