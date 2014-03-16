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
    'summary': fields.String,
    'score': fields.Float,
    'updated_at': DateTimeField,
    'created_at': DateTimeField,
    'concepts': fields.Nested({
        'url': fields.Url('concept'),
        'score': fields.Float
    }),
    'mentions': fields.Nested({
        'name': fields.String,
        'slug': fields.String
    }),
    'articles': fields.Nested({
        'url': fields.Url('article')
    }),
    'stories': fields.Nested({
        'url': fields.Url('story')
    })
}

story = {
    'id': fields.Integer,
    'url': fields.Url('story'),
    'title': fields.String,
    'image': fields.String,
    'images': fields.List(fields.String),
    'summary': fields.String,
    'updated_at': DateTimeField,
    'created_at': DateTimeField,
    'concepts': fields.Nested({
        'url': fields.Url('concept'),
        'score': fields.Float
    }),
    'mentions': fields.Nested({
        'name': fields.String,
        'slug': fields.String
    }),
    'events': fields.Nested({
        'url': fields.Url('event')
    }),
    'watchers': fields.Nested({
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
    'updated_at': DateTimeField,
    'stories': fields.Nested({
        'url': fields.Url('story'),
        'relatedness': fields.Float
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
        'url': fields.Url('source'),
        'name': fields.String
    }),
    'authors': fields.Nested({
        'url': fields.Url('author')
    }),
    'events': fields.Nested({
        'url': fields.Url('event')
    })
}

author = {
    'id': fields.Integer,
    'url': fields.Url('author'),
    'name': fields.String,
    'articles': fields.Nested({
        'url': fields.Url('article')
    })
}

source = {
    'id': fields.Integer,
    'url': fields.Url('source'),
    'name': fields.String,
    'ext_url': fields.String,
    'articles': fields.Nested({
        'url': fields.Url('article')
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
    return {
        'results': fields.Nested(representation_fields),
        'pagination': fields.Nested({
            'page': fields.Integer,
            'per_page': fields.Integer,
            'total_count': fields.Integer
        })
    }
