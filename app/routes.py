from flask import jsonify, request
from flask.ext.restful import Api, Resource, abort, marshal_with, marshal, fields, reqparse
from app import app
import models

DEFAULT_PER_PAGE = 15

api = Api(app)

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

paginate_parser = reqparse.RequestParser()
paginate_parser.add_argument('page', type=int, location='args', default=1)
paginate_parser.add_argument('per_page', type=int, location='args', default=DEFAULT_PER_PAGE)

class ListResource(Resource):
   
    _fields = {
        'results': fields.Integer,
        'page': fields.Integer,
        'per_page': fields.Integer,
        'max_page': fields.Integer,
        'items': fields.Nested(cluster_fields())
    }

    def fields(self):
        return ListResource._fields

    def get_page(self, page, per_page):
        raise NotImplementedError 

    def get(self): 
        args = paginate_parser.parse_args()
        result = self.get_page(args['page'], args['per_page']) 
        return marshal({
            'items': result.items,
            'results': len(result.items),
            'page': result.page,
            'per_page': result.per_page,
            'max_pages': result.pages
        }, self.fields())

class EventList(ListResource):
    def get_page(self, page, per_page):
        return models.Cluster.query.paginate(page, per_page)

class StoryList(ListResource):
    def fields(self):
        nfields = ListResource._fields
        nfields.update(items=
                fields.Nested(cluster_fields(members={'url': fields.Url('event')})))
        return nfields 
    def get_page(self, page, per_page):
        return models.Cluster.query.paginate(page, per_page)

class EntityList(ListResource):
    def fields(self):
        return { 'name': fields.String, 'slug': fields.String }
    def get_page(self, page, per_page):
        return models.Entity.query.paginate(page, per_page)

api.add_resource(EventList, '/events')
api.add_resource(StoryList, '/stories')
api.add_resource(EntityList, '/entities')

class Event(Resource):
    @marshal_with(cluster_fields())
    def get(self, id):
        result = models.Cluster.query.get(id)
        return result or not_found()
api.add_resource(Event, '/events/<int:id>')

class Story(Resource):
    @marshal_with(cluster_fields(members={'url': fields.Url('event')}))
    def get(self, id):
        result = models.Cluster.query.get(id)
        return result or not_found()
api.add_resource(Story, '/stories/<int:id>')

class Entity(Resource):
    @marshal_with({
        'name': fields.String,
        'slug': fields.String
    })
    def get(self, slug):
        result = models.Entity.query.get(slug)
        return result or not_found()
api.add_resource(Entity, '/entities/<string:slug>')
