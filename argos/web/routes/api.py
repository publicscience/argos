import argos.web.models as models

from argos.datastore import db
from argos.web.app import app
from argos.web.routes import api
from argos.web.routes.errors import not_found, unauthorized
from argos.web.routes.fields import EVENT_FIELDS, STORY_FIELDS, ENTITY_FIELDS, ARTICLE_FIELDS, AUTHOR_FIELDS, SOURCE_FIELDS, permitted_user_fields

from flask_security.core import current_user
from flask.ext.restful import Resource, marshal_with, fields, reqparse

# Whitelist of allowed request parameters.
page_parser = reqparse.RequestParser()
page_parser.add_argument('page', type=int, default=1)

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

class Latest(Resource):
    @marshal_with(EVENT_FIELDS)
    def get(self):
        args = page_parser.parse_args()
        results = models.Event.query.paginate(args['page']).items
        return results or not_found()
api.add_resource(Latest, '/latest')

class Trending(Resource):
    @marshal_with(EVENT_FIELDS)
    def get(self):
        args = page_parser.parse_args()
        results = models.Event.query.order_by(models.Event._score.desc()).paginate(args['page']).items
        return results or not_found()
api.add_resource(Trending, '/trending')

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
