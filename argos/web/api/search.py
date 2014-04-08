from argos.web.search import search
from argos.web.api import api, fields
from argos.web.api.errors import not_found
from argos.web.api.resources import page_parser, collection, PER_PAGE
from flask.ext.restful import Resource, reqparse

search_parser = reqparse.RequestParser()
search_parser.add_argument('types', type=str)

class Search(Resource):
    @collection(fields.search)
    def get(self, raw_query):
        args = search_parser.parse_args()
        page = page_parser.parse_args().get('page')
        raw_types = args.get('types') or 'event,story,concept'
        types = raw_types.split(',')

        if raw_query:
            results, total_count = search(raw_query, page, PER_PAGE, types=types)
            return results, total_count
        return not_found()
api.add_resource(Search, '/search/<string:raw_query>')
