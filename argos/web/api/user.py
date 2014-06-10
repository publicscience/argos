import argos.web.models as models

from argos.datastore import db
from argos.web.api import api, fields
from argos.web.api.oauth import oauth
from argos.web.api.resources import page_parser, collection, PER_PAGE
from argos.web.api.errors import not_found, unauthorized

from flask import request, abort
from flask.ext.restful import Resource, marshal_with, reqparse

parser = reqparse.RequestParser()

# temporary, expected to be replaced with mutable user settings.
parser.add_argument('something', type=str)

watching_parser = reqparse.RequestParser()
watching_parser.add_argument('story_id', type=int)

bookmarked_parser = reqparse.RequestParser()
bookmarked_parser.add_argument('event_id', type=int)


class CurrentUser(Resource):
    @oauth.require_oauth('userinfo')
    @marshal_with(fields.user)
    def get(self):
        return request.oauth.user

    @oauth.require_oauth('userinfo')
    @marshal_with(fields.user)
    def patch(self):
        current_user = request.oauth.user
        for key, val in parser.parse_args().items():
            setattr(current_user, key, val)
        db.session.commit()
        return '', 204
api.add_resource(CurrentUser, '/user')

class CurrentUserWatching(Resource):
    @oauth.require_oauth('userinfo')
    @marshal_with(fields.story)
    def get(self):
        current_user = request.oauth.user
        return current_user.watching
    @oauth.require_oauth('userinfo')
    def post(self):
        current_user = request.oauth.user
        id = watching_parser.parse_args()['story_id']
        story = models.Story.query.get(id)
        if not story:
            return not_found()
        current_user.watching.append(story)
        db.session.commit()
        return '', 201
class CurrentUserWatched(Resource):
    """
    For checking if an event is watched
    by the authenticated user.
    """
    @oauth.require_oauth('userinfo')
    def get(self, id):
        current_user = request.oauth.user
        if id in [watched.id for watched in current_user.watching]:
            return '', 204
        return abort(404)
    @oauth.require_oauth('userinfo')
    def delete(self, id):
        current_user = request.oauth.user
        story = models.Story.query.get(id)
        if not story or story not in current_user.watching:
            return not_found()
        current_user.watching.remove(story)
        db.session.commit()
        return '', 204
api.add_resource(CurrentUserWatching, '/user/watching')
api.add_resource(CurrentUserWatched, '/user/watching/<int:id>')

class CurrentUserFeed(Resource):
    """
    The authenticated user's feed is
    assembled from the latest events of the
    stories she is watching.
    """
    @oauth.require_oauth('userinfo')
    @marshal_with(fields.event)
    def get(self):
        # Get all the events which belong to stories that the user is watching.
        # This is so heinous, and probably very slow – but it works for now.
        # Eventually this will also have highly-promoted stories as well.
        current_user = request.oauth.user
        return models.Event.query.join(models.Event.stories).filter(models.Event.stories.any(models.Story.id.in_([story.id for story in current_user.watching]))).order_by(models.Event.created_at.desc()).all()
api.add_resource(CurrentUserFeed, '/user/feed')

class CurrentUserBookmarked(Resource):
    @oauth.require_oauth('userinfo')
    @marshal_with(fields.event)
    def get(self):
        return request.oauth.user.bookmarked
    @oauth.require_oauth('userinfo')
    def post(self):
        current_user = request.oauth.user
        id = bookmarked_parser.parse_args()['event_id']
        event = models.Event.query.get(id)
        if not event:
            return not_found()
        current_user.bookmarked.append(event)
        db.session.commit()
        return '', 201
class CurrentUserBookmark(Resource):
    """
    For checking if an event is bookmarked
    by the authenticated user.
    """
    @oauth.require_oauth('userinfo')
    def get(self, id):
        current_user = request.oauth.user
        if id in [bookmark.id for bookmark in current_user.bookmarked]:
            return '', 204
        return '', 404
    @oauth.require_oauth('userinfo')
    def delete(self, id):
        current_user = request.oauth.user
        event = models.Event.query.get(id)
        if not event or event not in current_user.bookmarked:
            return not_found()
        current_user.bookmarked.remove(event)
        db.session.commit()
        return '', 204
api.add_resource(CurrentUserBookmarked, '/user/bookmarked')
api.add_resource(CurrentUserBookmark, '/user/bookmarked/<int:id>')

class User(Resource):
    @marshal_with(fields.user)
    def get(self, id):
        result = models.User.query.get(id)
        return result or not_found()
api.add_resource(User, '/users/<int:id>')

class Users(Resource):
    @collection(fields.user)
    def get(self):
        page = page_parser.parse_args().get('page')
        results = models.User.query.paginate(page, per_page=PER_PAGE).items
        count = models.User.query.count()
        return results, count or not_found()
api.add_resource(Users, '/users')
