from flask.ext.restful import fields

class DateTimeField(fields.Raw):
    """
    Custom DateTime field, to return
    ISO 8601 formatted datetimes.
    (By default, Flask-Restful uses RFC822)
    """
    def format(self, value):
        return value.isoformat()

permitted_user_fields = {
    'id': fields.Integer,
    'image': fields.String,
    'name': fields.String,
    'updated_at': DateTimeField,
    'created_at': DateTimeField
}

EVENT_FIELDS = {
    'id': fields.Integer,
    'url': fields.Url('event'),
    'title': fields.String,
    'image': fields.String,
    'images': fields.List(fields.String),
    'summary': fields.String,
    'score': fields.Integer,
    'updated_at': DateTimeField,
    'created_at': DateTimeField,
    'entities': fields.Nested({
        'url': fields.Url('entity')
    }),
    'mentions': fields.Nested({
        'name': fields.String,
        'entity_slug': fields.String
    }),
    'articles': fields.Nested({
        'url': fields.Url('article')
    }),
    'stories': fields.Nested({
        'url': fields.Url('story')
    })
}

STORY_FIELDS = {
    'id': fields.Integer,
    'url': fields.Url('story'),
    'title': fields.String,
    'image': fields.String,
    'images': fields.List(fields.String),
    'summary': fields.String,
    'updated_at': DateTimeField,
    'created_at': DateTimeField,
    'entities': fields.Nested({
        'url': fields.Url('entity')
    }),
    'mentions': fields.Nested({
        'name': fields.String,
        'entity_slug': fields.String
    }),
    'events': fields.Nested({
        'url': fields.Url('event')
    }),
    'watchers': fields.Nested({
        'url': fields.Url('user')
    })
}

ENTITY_FIELDS = {
    'name': fields.String,
    'names': fields.List(fields.String),
    'slug': fields.String,
    'url': fields.Url('entity'),
    'summary': fields.String,
    'image': fields.String,
    'updated_at': DateTimeField,
    'stories': fields.Nested({
        'url': fields.Url('story')
    })
}

ARTICLE_FIELDS = {
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

AUTHOR_FIELDS = {
    'id': fields.Integer,
    'url': fields.Url('author'),
    'name': fields.String,
    'articles': fields.Nested({
        'url': fields.Url('article')
    })
}

SOURCE_FIELDS = {
    'id': fields.Integer,
    'url': fields.Url('source'),
    'name': fields.String,
    'ext_url': fields.String,
    'articles': fields.Nested({
        'url': fields.Url('article')
    })
}

SEARCH_FIELDS = {
    'id': fields.Integer,
    'title': fields.String,
    'image': fields.String,
    'summary': fields.String,
    'updated_at': DateTimeField,
    'created_at': DateTimeField,
    'type': fields.String
}
