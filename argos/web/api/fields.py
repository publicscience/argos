from flask.ext.restful import fields

class DateTimeField(fields.Raw):
    """
    Custom DateTime field, to return
    ISO 8601 formatted datetimes.
    (By default, Flask-Restful uses RFC822)
    """
    def format(self, value):
        return value.isoformat()

user = {
    'id': fields.Integer,
    'image': fields.String,
    'name': fields.String,
    'updated_at': DateTimeField,
    'created_at': DateTimeField
}

event = {
    'id': fields.Integer,
    'url': fields.Url('event'),
    'title': fields.String,
    'image': fields.String,
    'images': fields.List(fields.String),
    'summary': fields.List(fields.Nested({
        'sentence': fields.String,
        'source':   fields.String,
        'url':      fields.String
    }), attribute='summary_sentences'),
    'score': fields.Float,
    'updated_at': DateTimeField,
    'created_at': DateTimeField,
    'concepts': fields.Nested({
        'name': fields.String,
        'summary': fields.String,
        'image': fields.String,
        'url': fields.Url('concept'),
        'slug': fields.String,
        'score': fields.Float
    }, attribute='top_concepts'),
    'mentions': fields.Nested({
        'id': fields.Integer,
        'name': fields.String,
        'slug': fields.String
    }),
    'articles': fields.Nested({
        'id': fields.Integer,
        'title': fields.String,
        'ext_url': fields.String,
        'url': fields.Url('article'),
        'source': fields.Nested({
            'name': fields.String
        })
    }),
    'stories': fields.Nested({
        'id': fields.Integer,
        'url': fields.Url('story')
    })
}

story = {
    'id': fields.Integer,
    'url': fields.Url('story'),
    'title': fields.String,
    'image': fields.String,
    'images': fields.List(fields.String),
    'summary': fields.List(fields.String, attribute='summary_sentences'),
    'updated_at': DateTimeField,
    'created_at': DateTimeField,
    'concepts': fields.Nested({
        'url': fields.Url('concept'),
        'slug': fields.String,
        'score': fields.Float
    }, attribute='top_concepts'),
    'mentions': fields.Nested({
        'id': fields.Integer,
        'name': fields.String,
        'slug': fields.String
    }),
    'events': fields.Nested({
        'id': fields.Integer,
        'title': fields.String,
        'score': fields.Float,
        'updated_at': DateTimeField,
        'created_at': DateTimeField,
        'num_articles': fields.Integer,
        'url': fields.Url('event')
    }),
    'watchers': fields.Nested({
        'id': fields.Integer,
        'url': fields.Url('user')
    })
}

concept = {
    'name': fields.String,
    'names': fields.List(fields.String),
    'slug': fields.String,
    'url': fields.Url('concept'),
    'summary': fields.String,
    'image': fields.String,
    'commonness': fields.Float,
    'updated_at': DateTimeField,
    'profile': fields.Raw,
    'sources': fields.List(fields.String),
    'stories': fields.Nested({
        'id': fields.Integer,
        'title': fields.String,
        'updated_at': DateTimeField,
        'created_at': DateTimeField,
        'url': fields.Url('story'),
        'relatedness': fields.Float,
        'num_events': fields.Integer
    })
}

article = {
    'id': fields.Integer,
    'url': fields.Url('article'),
    'title': fields.String,
    'image': fields.String,
    'ext_url': fields.String,
    'created_at': DateTimeField,
    'updated_at': DateTimeField,
    'source': fields.Nested({
        'id': fields.Integer,
        'url': fields.Url('source'),
        'name': fields.String
    }),
    'authors': fields.Nested({
        'id': fields.Integer,
        'url': fields.Url('author')
    }),
    'events': fields.Nested({
        'id': fields.Integer,
        'url': fields.Url('event')
    })
}

author = {
    'id': fields.Integer,
    'url': fields.Url('author'),
    'name': fields.String,
    'articles': fields.Nested({
        'id': fields.Integer,
        'url': fields.Url('article')
    })
}

source = {
    'id': fields.Integer,
    'url': fields.Url('source'),
    'name': fields.String,
    'ext_url': fields.String,
    'articles': fields.Nested({
        'id': fields.Integer,
        'url': fields.Url('article')
    }),
    'feeds': fields.Nested({
        'id': fields.Integer,
        'url': fields.Url('feed'),
        'ext_url': fields.String
    })
}

search = {
    'id': fields.Integer,
    'title': fields.String,
    'slug': fields.String, # for concepts
    'name': fields.String, # for concepts
    'image': fields.String,
    'summary': fields.String,
    'updated_at': DateTimeField,
    'created_at': DateTimeField,
    'type': fields.String,
    'rank': fields.Float,
    # the actual URL creation is handled by the search route
    'url': fields.String
}

def collection(representation_fields):
    """
    A common resource format
    for collections.

    Includes the results and pagination info.
    """
    return {
        'results': fields.Nested(representation_fields),
        'pagination': fields.Nested({
            'page': fields.Integer,
            'per_page': fields.Integer,
            'total_count': fields.Integer
        })
    }
