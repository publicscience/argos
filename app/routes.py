from flask import jsonify, request
from flask.ext.restful import Api, Resource, abort, marshal_with, fields
from app import app
import models

api = Api(app)

@app.errorhandler(404)
def internal_error(error):
    return jsonify(status=404, message='The resource you requested was not found.'), 404

@app.errorhandler(500)
def internal_error(error):
    app.logger.exception(error)
    return jsonify(status=500, message='Internal server error.'), 500

def not_found():
    return abort(404, message='The resource you requested, %s, was not found.' % request.path, status=404)

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
    members_ = {
        'type': fields.String,
        'title': fields.String,
        'url': fields.String,
        'id': fields.Integer,
        'created_at': DateTimeField
    }
    members_.update(members)

    fields_ = {
        'id': fields.Integer,
        'title': fields.String,
        'summary': fields.String,
        'tag': fields.String,
        'updated_at': DateTimeField,
        'created_at': DateTimeField,
        'members': fields.Nested(members_),
        'entities': fields.Nested({
            'name': fields.String,
            'url': fields.Url('entity')
        })
    }
    fields_.update(custom)
    return fields_

class Event(Resource):
    @marshal_with(cluster_fields())
    def get(self, id):
        result = models.Cluster.query.filter_by(tag='event', id=id).first()
        return result or not_found()
api.add_resource(Event, '/events/<int:id>')

class Story(Resource):
    @marshal_with(cluster_fields(members={'url': fields.Url('event')}))
    def get(self, id):
        result = models.Cluster.query.filter_by(tag='story', id=id).first()
        return result or not_found()
api.add_resource(Story, '/stories/<int:id>')

class Entity(Resource):
    @marshal_with({
        'name': fields.String,
        'slug': fields.String
    })
    def get(self, slug):
        result = models.Entity.query.filter_by(slug=slug).first()
        return result or not_found()
api.add_resource(Entity, '/entities/<string:slug>')
