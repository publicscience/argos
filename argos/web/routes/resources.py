import argos.web.models as models

from argos.datastore import db
from argos.web.app import app
from argos.web.routes import api, fields
from argos.web.routes.errors import not_found, unauthorized

from flask_security.core import current_user
from flask.ext.restful import Resource, marshal_with, reqparse
from functools import wraps

# Whitelist of allowed request parameters.
page_parser = reqparse.RequestParser()
page_parser.add_argument('page', type=int, default=1)

PER_PAGE = 20

def collection(member_fields):
    """
    A decorator for handling collection/list resources;
    this will automatically format pagination information
    in the response.
    """
    def decorator(f):
        @marshal_with(fields.collection(member_fields))
        @wraps(f)
        def decorated(*args, **kwargs):
            page = page_parser.parse_args().get('page')
            results, count = f(*args, **kwargs)
            return {'results': results,
                    'pagination': {
                        'page': page,
                        'per_page': PER_PAGE,
                        'total_count': count
                    }}
        return decorated
    return decorator

class Event(Resource):
    @marshal_with(fields.event)
    def get(self, id):
        result = models.Event.query.get(id)
        return result or not_found()
class Events(Resource):
    @collection(fields.event)
    def get(self):
        page = page_parser.parse_args().get('page')
        results = models.Event.query.paginate(page, per_page=PER_PAGE).items
        count = models.Event.query.count()
        return results, count or not_found()
api.add_resource(Event, '/events/<int:id>')
api.add_resource(Events, '/events')

class Latest(Resource):
    @collection(fields.event)
    def get(self):
        page = page_parser.parse_args().get('page')
        results = models.Event.query.paginate(page, per_page=PER_PAGE).items
        count = models.Event.query.count()
        return results, count or not_found()
api.add_resource(Latest, '/latest')

class Trending(Resource):
    @collection(fields.event)
    def get(self):
        page = page_parser.parse_args().get('page')
        results = models.Event.query.order_by(models.Event._score.desc()).paginate(page, per_page=PER_PAGE).items
        count = models.Event.query.count()
        return results, count or not_found()
api.add_resource(Trending, '/trending')

class Story(Resource):
    @marshal_with(fields.story)
    def get(self, id):
        result = models.Story.query.get(id)
        return result or not_found()
class Stories(Resource):
    @collection(fields.story)
    def get(self):
        page = page_parser.parse_args().get('page')
        results = models.Story.query.paginate(page, per_page=PER_PAGE).items
        count = models.Story.query.count()
        return results, count or not_found()
class StoryWatchers(Resource):
    @marshal_with(fields.user)
    def get(self, id):
        result = models.Story.query.get(id)
        return result.watchers or not_found()
    def post(self, id):
        if current_user.is_authenticated():
            result = models.Story.query.get(id)
            result.watchers.append(current_user)
            db.session.commit()
            return '', 201
        else:
            return unauthorized()
    def delete(self, id):
        if current_user.is_authenticated():
            result = models.Story.query.get(id)
            result.watchers.remove(current_user)
            db.session.commit()
            return '', 204
        else:
            return unauthorized()
api.add_resource(Story, '/stories/<int:id>')
api.add_resource(Stories, '/stories')
api.add_resource(StoryWatchers, '/stories/<int:id>/watchers')


class Entity(Resource):
    @marshal_with(fields.entity)
    def get(self, slug):
        result = models.Entity.query.get(slug)
        return result or not_found()
api.add_resource(Entity, '/entities/<string:slug>')


class Article(Resource):
    @marshal_with(fields.article)
    def get(self, id):
        result = models.Article.query.get(id)
        return result or not_found()
api.add_resource(Article, '/articles/<int:id>')


class Author(Resource):
    @marshal_with(fields.author)
    def get(self, id):
        result = models.Author.query.get(id)
        return result or not_found()
api.add_resource(Author, '/authors/<int:id>')


class Source(Resource):
    @marshal_with(fields.source)
    def get(self, id):
        result = models.Source.query.get(id)
        return result or not_found()
api.add_resource(Source, '/sources/<int:id>')
