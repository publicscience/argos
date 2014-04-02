import argos.web.models as models

from argos.datastore import db
from argos.web.api import api, fields
from argos.web.api.errors import not_found
from argos.web.api.resources import page_parser, collection, PER_PAGE
from flask import url_for
from flask.ext.restful import Resource, reqparse

from sqlalchemy import select, func, literal, union_all

search_parser = reqparse.RequestParser()
search_parser.add_argument('types', type=str)

class Search(Resource):
    @collection(fields.search)
    def get(self, raw_query):
        """
        Full-text search.
        Under the hood this takes advantage of PostgreSQL's full-text
        search functionality.

        This is still a fairly simple search and can be tuned quite a bit
        for better results.
        """

        args = search_parser.parse_args()
        page = page_parser.parse_args().get('page')
        raw_types = args.get('types') or 'event,story,concept'
        types = raw_types.split(',')

        if raw_query:
            # Basic 'tokenization';
            # psql requires the query string be formed as tokens
            # divided by boolean operators. Here we just use & (AND),
            # but it also supports | (OR) and ! (NOT).
            # The simple approach here is just splitting by whitespace,
            # then rejoining with &.
            # For example "senator foobar" becomes "senator & foobar".
            query = ' & '.join(raw_query.strip().split())

            # See http://www.postgresql.org/docs/9.3/static/textsearch-controls.html
            # for more on how these weights affect ranking.
            # These are the default weights.
            weights = '{0.1, 0.2, 0.4, 1.0}'

            # Keep track of the individual SQL queries;
            # later they are combined into one complete query.
            sql_queries = []

            # Flask-SQLAlchemy doesn't provide the flexibility needed to use psql's full text,
            # so using SQLAlchemy directly.
            # Note that using `select` directly like we are here does not automatically map the resulting rows to objects. We get tuples instead, though each row is still accessible by its name, i.e. event.title.

            if 'event' in types:
                ev_sql = db.select([
                # Select all properties of the Event model.
                            models.Event.id,
                            models.Event.title,
                            models.Event.image,
                            models.Event.summary,
                            models.Event.updated_at,
                            models.Event.created_at,
                # We have to include these dummy values so that
                # each SELECT statement has the same number of columns.
                            literal(None).label('slug'),
                            literal(None).label('name'),
                # We also additionally include a `type` so we can distinguish Events from Stories from Concepts.
                            literal('event').label('type'),
                # We also include a 'rank' column which is calculated by psql's full text ranking functions. This is used to sort results.
                            db.func.ts_rank_cd(
                                weights,
                                db.func.to_tsvector('english', models.Event.summary),
                                db.func.to_tsquery(query)).label('rank')
                         ],
                # Specify there 'where' clause; `match` exposes psql's full text searching capability.
                # The parens wrapping each match statement is necessary to use the | as an OR operator.
                         whereclause=((models.Event.title.match(query)) | (models.Event.summary.match(query))))
                sql_queries.append(ev_sql)

            # We could use the object mapper in this way and get the rows mapped to objects automatically, i.e. work with Event objects instead of tuples. But then we don't have access to the temporary `rank` attribute which is needed for sorting later.
            if 'story' in types:
                st_sql = db.select([
                            models.Story.id,
                            models.Story.title,
                            models.Story.image,
                            models.Story.summary,
                            models.Story.updated_at,
                            models.Story.created_at,
                            literal(None).label('slug'),
                            literal(None).label('name'),
                            literal('story').label('type'),
                            db.func.ts_rank_cd(
                                weights,
                                db.func.to_tsvector('english', models.Story.summary),
                                db.func.to_tsquery(query)).label('rank')
                         ],
                         whereclause=((models.Story.title.match(query)) | (models.Story.summary.match(query))))
                sql_queries.append(st_sql)

            if 'concept' in types:
                en_sql = db.select([
                            literal(0).label('id'),
                            literal('').label('title'),
                            models.Concept.image,
                            models.Concept.summary,
                            models.Concept.updated_at,
                            models.Concept.created_at,
                            models.Concept.slug,
                            models.Concept.name,
                            literal('concept').label('type'),
                            db.func.ts_rank_cd(
                                weights,
                                db.func.to_tsvector('english', models.Concept.summary),
                                db.func.to_tsquery(query)).label('rank')
                         ],
                         whereclause=((models.Concept.name.match(query)) | (models.Concept.summary.match(query))))
                sql_queries.append(en_sql)

            # Finally we combine the queries and then
            # order things by the psql calculated rank, descending.
            sql_query = union_all(*sql_queries).order_by(db.desc('rank'))

            # Get the total number of results for this search.
            total_count = db.engine.execute(sql_query.alias('matching_results').count()).scalar()

            # Then we execute the query, with pagination.
            results = db.engine.execute(sql_query.limit(PER_PAGE).offset((page-1)*PER_PAGE)).fetchall()

            # Process the result rows to match the specified fields.
            results_ = []
            for r in results:
                r = dict(r)

                # Build the url for the result.
                if (r['type'] == 'concept'):
                    r['url'] = url_for(r['type'], slug=r['id'])
                else:
                    r['url'] = url_for(r['type'], id=r['id'])

                results_.append(r)

            return results_, total_count
        return not_found()
api.add_resource(Search, '/search/<string:raw_query>')

