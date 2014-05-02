import argos.web.models as models

from argos.datastore import db
from argos.web.api import api, fields
from argos.web.api.errors import not_found, unauthorized

from flask_security.core import current_user
from flask.ext.restful import Resource, marshal_with, reqparse
from functools import wraps
from datetime import datetime

# Whitelist of allowed request parameters.
page_parser = reqparse.RequestParser()
page_parser.add_argument('page', type=int, default=1)

# Request parameters specifically for feeds,
# including `from` and `to` for defining date ranges
# of results (date format is 2014-01-31).
feed_parser = reqparse.RequestParser()
feed_parser.add_argument('from', type=str)
feed_parser.add_argument('to', type=str)

def parse_date_range():
    args = feed_parser.parse_args()
    from_date = args.get('from', None)
    to_date = args.get('to', None)

    #if raw_from_date:
        #from_date = datetime.strptime(raw_from_date, '%d-%m-%Y')

    #if raw_to_date:
        #to_date = datetime.strptime(raw_to_date, '%d-%m-%Y')

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

        feed_args = feed_parser.parse_args()
        from_date = feed_args.get('from', None)
        to_date = feed_args.get('to', None)

        if from_date and to_date:
            results = models.Event.query.filter(models.Event.created_at.between(from_date, to_date)).paginate(page, per_page=PER_PAGE).items
        elif from_date:
            results = models.Event.query.filter(models.Event.created_at >= from_date).paginate(page, per_page=PER_PAGE).items
        elif to_date:
            results = models.Event.query.filter(models.Event.created_at <= to_date).paginate(page, per_page=PER_PAGE).items
        else:
            results = models.Event.query.paginate(page, per_page=PER_PAGE).items

        count = models.Event.query.count()
        return results, count or not_found()
api.add_resource(Latest, '/latest')

class Trending(Resource):
    @collection(fields.event)
    def get(self):
        page = page_parser.parse_args().get('page')

        feed_args = feed_parser.parse_args()
        from_date = feed_args.get('from', None)
        to_date = feed_args.get('to', None)

        if from_date and to_date:
            results = models.Event.query.filter(models.Event.created_at.between(from_date, to_date)).order_by(models.Event._score.desc()).paginate(page, per_page=PER_PAGE).items
        elif from_date:
            results = models.Event.query.filter(models.Event.created_at >= from_date).order_by(models.Event._score.desc()).paginate(page, per_page=PER_PAGE).items
        elif to_date:
            results = models.Event.query.filter(models.Event.created_at <= to_date).order_by(models.Event._score.desc()).paginate(page, per_page=PER_PAGE).items
        else:
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


class Concept(Resource):
    @marshal_with(fields.concept)
    def get(self, slug):
        result = models.Concept.query.get(slug)
        return result or not_found()
api.add_resource(Concept, '/concepts/<string:slug>')


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
