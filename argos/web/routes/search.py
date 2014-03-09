import argos.web.models as models

from argos.datastore import db
from argos.web.app import app
from argos.web.routes.fields import SEARCH_FIELDS
from argos.web.routes.errors import not_found
from flask import jsonify, url_for
from flask.ext.restful import reqparse, marshal

from sqlalchemy import select, func, literal

search_parser = reqparse.RequestParser()
search_parser.add_argument('query', type=str)
search_parser.add_argument('types', type=str)

@app.route('/search')
def search():
    """
    Full-text search.
    Under the hood this takes advantage of PostgreSQL's full-text
    search functionality.

    This is still a fairly simple search and can be tuned quite a bit
    for better results.
    """

    args = search_parser.parse_args()
    raw_query = args['query']
    raw_types = args.get('types') or 'event,story,entity'
    types = raw_types.split(',')

    if raw_query:
        # Basic 'tokenization';
        # psql requires the query string be formed as tokens
        # divided by boolean operators. Here we just use & (AND),
        # but it also supports | (OR) and ! (NOT).
        # The simple approach here is just splitting by whitespace,
        # then rejoining with &.
        query = ' & '.join(raw_query.strip().split())

        # See http://www.postgresql.org/docs/9.3/static/textsearch-controls.html
        # for more on how these weights affect ranking.
        # These are the default weights.
        weights = '{0.1, 0.2, 0.4, 1.0}'

        # Keep track of results.
        results = []

        # Flask-SQLAlchemy doesn't provide the flexibility needed to use psql's full text,
        # so using SQLAlchemy directly.
        # Note that using `select` directly like we are here does not automatically map the resulting rows to objects. We get tuples instead, though each row is still accessible by its name, i.e. event.title.

        if 'event' in types:
            ev_sql = db.select([
            # Select all properties of the Event model.
                        models.Event,
            # We also additionally include a `type` so we can distinguish Events from Stories from Entities.
                        literal('event').label('type'),
            # We also include a 'rank' column which is calculated by psql's full text ranking functions. This is used to sort results.
                        db.func.ts_rank_cd(
                            weights,
                            db.func.to_tsvector('english', models.Event.summary),
                            db.func.to_tsquery(query)).label('rank')
                     ],
            # Specify there 'where' clause; `match` exposes psql's full text searching capability.
            # The parens wrapping each match statement is necessary to use the | as an OR operator.
                     ((models.Event.title.match(query)) | (models.Event.summary.match(query))))\
                     .order_by(db.desc('rank'))
            # Finally we order things by the psql calculated rank, descending.
            results.extend(db.engine.execute(ev_sql).fetchall())

        # We could use the object mapper in this way and get the rows mapped to objects automatically, i.e. work with Event objects instead of tuples. But then we don't have access to the temporary `rank` attribute which is needed for sorting later.
        #results = models.Event.query.from_statement(ev_sql).all()

        if 'story' in types:
            st_sql = db.select([
                        models.Story,
                        literal('story').label('type'),
                        db.func.ts_rank_cd(
                            weights,
                            db.func.to_tsvector('english', models.Story.summary),
                            db.func.to_tsquery(query)).label('rank')
                     ],
                     ((models.Story.title.match(query)) | (models.Story.summary.match(query))))\
                     .order_by(db.desc('rank'))
            results.extend(db.engine.execute(st_sql).fetchall())

        if 'entity' in types:
            en_sql = db.select([
                        models.Entity,
                        models.Entity.slug.label('id'),
                        models.Entity.name.label('title'),
                        literal('entity').label('type'),
                        db.func.ts_rank_cd(
                            weights,
                            db.func.to_tsvector('english', models.Entity.summary),
                            db.func.to_tsquery(query)).label('rank')
                     ],
                     ((models.Entity.name.match(query)) | (models.Entity.summary.match(query))))\
                     .order_by(db.desc('rank'))
            results.extend(db.engine.execute(en_sql).fetchall())

        # Sort results by rank in descending order.
        results.sort(key=lambda x: x.rank, reverse=True)

        # Process the result rows to match the specified fields.
        results_ = []
        for r in results:
            d = marshal(r, SEARCH_FIELDS)

            # Build the url for the result.
            if (r.type == 'entity'):
                d['url'] = url_for(d['type'], slug=d['id'])
            else:
                d['url'] = url_for(d['type'], id=d['id'])

            results_.append(d)

        return jsonify({'results':results_, 'count':len(results_)})
    return not_found()


