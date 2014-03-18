Events
------

**Get all events (paginated)**::

    GET /events

Parameters

+---------------+--------+----------------------------------+
| Name          | Type   | Description                      |
+===============+========+==================================+
| page          | int    | The page of events to fetch.     |
+---------------+--------+----------------------------------+

Example response

.. code-block:: json

    {
        "results": [{
            "id": 1,
            "url": "/events/1",
            "title": "Kerry leads Syrian peace talks",
            "image": "https://s3.amazonaws.com/argos/189751513.jpg",
            "images": ["https://s3.amazonaws.com/argos/2487149.jpg", "https://s3.amazonaws.com/argos/1248979.jpg"],
            "summary": "Secretary of State John Kerry said on Sunday that Iran might play...",
            "score": "71283.0",
            "updated_at": "2014-02-07T23:42:15.581374",
            "created_at": "2014-02-06T20:55:54.597459",
            "concepts": [{
                "slug": "john-kerry",
                "url": "/concepts/john-kerry",
                "score": "0.67"
            }],
            "mentions": [{
                "id": 1,
                "name": "John Kerry",
                "slug": "john-kerry"
            }],
            "articles": [{
                "id": 1,
                "url": "/articles/1"
            }],
            "stories": [{
                "id": 1,
                "url": "/stories/1"
            }]
        }],
        "pagination": {
            "page": 1,
            "per_page": 20,
            "total_count": 240
        }
    }


-----

**Get a single event**::

    GET /events/:id

Example response

.. code-block:: json

    {
        "id": 1,
        "url": "/events/1",
        "title": "Kerry leads Syrian peace talks",
        "image": "https://s3.amazonaws.com/argos/189751513.jpg",
        "images": ["https://s3.amazonaws.com/argos/2487149.jpg", "https://s3.amazonaws.com/argos/1248979.jpg"],
        "summary": "Secretary of State John Kerry said on Sunday that Iran might play...",
        "score": "71283.0",
        "updated_at": "2014-02-07T23:42:15.581374",
        "created_at": "2014-02-06T20:55:54.597459",
        "concepts": [{
            "slug": "john-kerry",
            "url": "/concepts/john-kerry",
            "score": "0.67"
        }],
        "mentions": [{
            "id": 1,
            "name": "John Kerry",
            "slug": "john-kerry"
        }],
        "articles": [{
            "id": 1,
            "url": "/articles/1"
        }],
        "stories": [{
            "id": 1,
            "url": "/stories/1"
        }]
    }
