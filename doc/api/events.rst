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

    [
        {
            "id": 1,
            "url": "/events/1",
            "title": "Kerry leads Syrian peace talks",
            "image": "https://s3.amazonaws.com/argos/189751513.jpg",
            "summary": "Secretary of State John Kerry said on Sunday that Iran might play...",
            "updated_at": "2014-02-07T23:42:15.581374",
            "created_at": "2014-02-06T20:55:54.597459",
            "entities": [{
                "url": "/entities/john-kerry"
            }],
            "articles": [{
                "url": "/articles/1"
            }],
            "stories": [{
                "url": "/stories/1"
            }]
        }
    ]

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
        "summary": "Secretary of State John Kerry said on Sunday that Iran might play...",
        "updated_at": "2014-02-07T23:42:15.581374",
        "created_at": "2014-02-06T20:55:54.597459",
        "entities": [{
            "url": "/entities/john-kerry"
        }],
        "articles": [{
            "url": "/articles/1"
        }],
        "stories": [{
            "url": "/stories/1"
        }]
    }
