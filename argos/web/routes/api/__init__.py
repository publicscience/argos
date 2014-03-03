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

EVENT_FIELDS = {
    'id': fields.Integer,
    'url': fields.Url('event'),
    'title': fields.String,
    'image': fields.String,
    'summary': fields.String,
    'updated_at': DateTimeField,
    'created_at': DateTimeField,
    'entities': fields.Nested({
        'url': fields.Url('entity')
    }),
    'articles': fields.Nested({
        'url': fields.Url('article')
    }),
    'stories': fields.Nested({
        'url': fields.Url('story')
    })
}

STORY_FIELDS = {
    'id': fields.Integer,
    'url': fields.Url('story'),
    'title': fields.String,
    'image': fields.String,
    'summary': fields.String,
    'updated_at': DateTimeField,
    'created_at': DateTimeField,
    'entities': fields.Nested({
        'url': fields.Url('entity')
    }),
    'events': fields.Nested({
        'url': fields.Url('event')
    }),
    'watchers': fields.Nested({
        'url': fields.Url('user')
    })
}

ENTITY_FIELDS = {
    'name': fields.String,
    'slug': fields.String,
    'url': fields.Url('entity'),
    'updated_at': DateTimeField,
    'stories': fields.Nested({
        'url': fields.Url('story')
    })
}

ARTICLE_FIELDS = {
    'id': fields.Integer,
    'url': fields.Url('article'),
    'title': fields.String,
    'image': fields.String,
    'ext_url': fields.String,
    'created_at': DateTimeField,
    'updated_at': DateTimeField,
    'source': fields.Nested({
        'url': fields.Url('source'),
        'name': fields.String
    }),
    'authors': fields.Nested({
        'url': fields.Url('author')
    }),
    'events': fields.Nested({
        'url': fields.Url('event')
    })
}

AUTHOR_FIELDS = {
    'id': fields.Integer,
    'url': fields.Url('author'),
    'name': fields.String,
    'articles': fields.Nested({
        'url': fields.Url('article')
    })
}

SOURCE_FIELDS = {
    'id': fields.Integer,
    'url': fields.Url('source'),
    'name': fields.String,
    'ext_url': fields.String,
    'articles': fields.Nested({
        'url': fields.Url('article')
    })
}

class Event(Resource):
    @marshal_with(EVENT_FIELDS)
    def get(self, id):
        result = models.Event.query.get(id)
        return result or not_found()
class Events(Resource):
    @marshal_with(EVENT_FIELDS)
    def get(self):
        args = page_parser.parse_args()
        results = models.Event.query.paginate(args['page']).items
        return results or not_found()
api.add_resource(Event, '/events/<int:id>')
api.add_resource(Events, '/events')


class Story(Resource):
    @marshal_with(STORY_FIELDS)
    def get(self, id):
        result = models.Story.query.get(id)
        return result or not_found()
class Stories(Resource):
    @marshal_with(STORY_FIELDS)
    def get(self):
        args = page_parser.parse_args()
        results = models.Story.query.paginate(args['page']).items
        return results or not_found()
class StoryWatchers(Resource):
    from argos.web.routes.api.user import permitted_user_fields
    @marshal_with(permitted_user_fields)
    def get(self, id):
        result = models.Story.query.get(id)
        return result.watchers or not_found()
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
    @marshal_with(ENTITY_FIELDS)
    def get(self, slug):
        result = models.Entity.query.get(slug)
        return result or not_found()
api.add_resource(Entity, '/entities/<string:slug>')


class Article(Resource):
    @marshal_with(ARTICLE_FIELDS)
    def get(self, id):
        result = models.Article.query.get(id)
        return result or not_found()
api.add_resource(Article, '/articles/<int:id>')


class Author(Resource):
    @marshal_with(AUTHOR_FIELDS)
    def get(self, id):
        result = models.Author.query.get(id)
        return result or not_found()
api.add_resource(Author, '/authors/<int:id>')


class Source(Resource):
    @marshal_with(SOURCE_FIELDS)
    def get(self, id):
        result = models.Source.query.get(id)
        return result or not_found()
api.add_resource(Source, '/sources/<int:id>')

from argos.web.routes.api import user, search
