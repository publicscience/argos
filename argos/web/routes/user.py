import argos.web.models as models

from argos.datastore import db
from argos.web.routes import api
from argos.web.routes.api import page_parser
from argos.web.routes.fields import STORY_FIELDS, EVENT_FIELDS, permitted_user_fields
from argos.web.routes.errors import not_found, unauthorized

from flask import request, abort
from flask_security.core import current_user
from flask.ext.restful import Resource, marshal_with, fields, reqparse

parser = reqparse.RequestParser()

# temporary, expected to be replaced with mutable user settings.
parser.add_argument('something', type=str)

watching_parser = reqparse.RequestParser()
watching_parser.add_argument('story_id', type=int)

bookmarked_parser = reqparse.RequestParser()
bookmarked_parser.add_argument('event_id', type=int)


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
    def post(self):
        if current_user.is_authenticated():
            id = watching_parser.parse_args()['story_id']
            story = models.Story.query.get(id)
            if not story:
                return not_found()
            current_user.watching.append(story)
            db.session.commit()
            return '', 201
        else:
            return unauthorized()
    def delete(self):
        if current_user.is_authenticated():
            id = watching_parser.parse_args()['story_id']
            story = models.Story.query.get(id)
            if not story or story not in current_user.watching:
                return not_found()
            current_user.watching.remove(story)
            db.session.commit()
            return '', 204
        else:
            return unauthorized()
class CurrentUserWatched(Resource):
    """
    For checking if an event is watched
    by the authenticated user.
    """
    def get(self, id):
        if current_user.is_authenticated():
            if id in [watched.id for watched in current_user.watching]:
                return '', 204
            return abort(404)
        else:
            return unauthorized()
api.add_resource(CurrentUserWatching, '/user/watching')
api.add_resource(CurrentUserWatched, '/user/watching/<int:id>')

class CurrentUserFeed(Resource):
    """
    The authenticated user's feed is
    assembled from the latest events of the
    stories she is watching.
    """
    @marshal_with(EVENT_FIELDS)
    def get(self):
        if current_user.is_authenticated():
            # Get all the events which belong to stories that the user is watching.
            # This is so heinous, and probably very slow – but it works for now.
            return models.Event.query.join(models.Event.stories).filter(models.Event.stories.any(models.Story.id.in_([story.id for story in current_user.watching]))).all()
        else:
            return unauthorized()
api.add_resource(CurrentUserFeed, '/user/feed')

class CurrentUserBookmarked(Resource):
    @marshal_with(EVENT_FIELDS)
    def get(self):
        if current_user.is_authenticated():
            return current_user.bookmarked
        else:
            return unauthorized()
    def post(self):
        if current_user.is_authenticated():
            id = bookmarked_parser.parse_args()['event_id']
            event = models.Event.query.get(id)
            if not event:
                return not_found()
            current_user.bookmarked.append(event)
            db.session.commit()
            return '', 201
        else:
            return unauthorized()
    def delete(self):
        if current_user.is_authenticated():
            id = bookmarked_parser.parse_args()['event_id']
            event = models.Event.query.get(id)
            if not event or event not in current_user.bookmarked:
                return not_found()
            current_user.bookmarked.remove(event)
            db.session.commit()
            return '', 204
        else:
            return unauthorized()
class CurrentUserBookmark(Resource):
    """
    For checking if an event is bookmarked
    by the authenticated user.
    """
    def get(self, id):
        if current_user.is_authenticated():
            if id in [bookmark.id for bookmark in current_user.bookmarked]:
                return '', 204
            return abort(404)
        else:
            return unauthorized()
api.add_resource(CurrentUserBookmarked, '/user/bookmarked')
api.add_resource(CurrentUserBookmark, '/user/bookmarked/<int:id>')

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


