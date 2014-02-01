from web.app import app

from database import models

from flask import jsonify, request
from flask.ext.restful import Api, Resource, abort, marshal_with, fields, reqparse, marshal

api = Api(app)

# Whitelist of allowed request parameters.
parser = reqparse.RequestParser()
parser.add_argument('page', type=int, default=1)

@app.errorhandler(404)
def internal_error(error):
    return jsonify(status=404, message='The resource you requested was not found.'), 404

@app.errorhandler(500)
def internal_error(error):
    app.logger.exception(error)
    return jsonify(status=500, message='Internal server error.'), 500

def not_found():
    return abort(404, message='The resource you requested, {0}, was not found.'.format(request.path), status=404)

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
        'tag': fields.String,
        'updated_at': DateTimeField,
        'created_at': DateTimeField,
        'entities': fields.Nested({
            'name': fields.String,
            'url': fields.Url('entity')
        })
    }

    if members is not None:
        members_ = {
            'type': fields.String,
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
        result = models.Cluster.query.get(id)
        return result or not_found()
class EventList(Resource):
    # Doesn't need to return members, i.e. individual articles.
    # That slows it down by a lot, and they aren't necessary here.
    @marshal_with(cluster_fields(members=None))
    def get(self):
        args = parser.parse_args()
        results = models.Cluster.query.filter_by(tag='event').paginate(args['page']).items
        return results or not_found()
api.add_resource(Event, '/events/<int:id>')
api.add_resource(EventList, '/events')

class Story(Resource):
    @marshal_with(cluster_fields(members={'url': fields.Url('event')}))
    def get(self, id):
        result = models.Cluster.query.get(id)
        return result or not_found()
class StoryList(Resource):
    @marshal_with(cluster_fields(members={'url': fields.Url('event')}))
    def get(self):
        args = parser.parse_args()
        results = models.Cluster.query.filter_by(tag='story').paginate(args['page']).items
        return results or not_found()
api.add_resource(Story, '/stories/<int:id>')
api.add_resource(StoryList, '/stories')

class Entity(Resource):
    @marshal_with({
        'name': fields.String,
        'slug': fields.String
    })
    def get(self, slug):
        result = models.Entity.query.get(slug)
        return result or not_found()
api.add_resource(Entity, '/entities/<string:slug>')
