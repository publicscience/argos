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
            "title": "Kerry leads Syrian peace talks",
            "image": "https://s3.amazonaws.com/argos/189751513.jpg",
            "summary": "Secretary of State John Kerry said on Sunday that Iran might play...",
            "updated_at": "2014-02-07T23:42:15.581374",
            "created_at": "2014-02-06T20:55:54.597459",
            "entities": [{
                "name": "John Kerry",
                "url": "https://api.argos.so/entities/john-kerry"
            }]
        }
    ]

-----

**Get a single event**::

    GET /events/:id

Example response

.. code-block:: json

    [
        {
            "id": 1,
            "title": "Kerry leads Syrian peace talks",
            "image": "https://s3.amazonaws.com/argos/189751513.jpg",
            "summary": "Secretary of State John Kerry said on Sunday that Iran might play...",
            "updated_at": "2014-02-07T23:42:15.581374",
            "created_at": "2014-02-06T20:55:54.597459",
            "entities": [{
                "name": "John Kerry",
                "url": "https://api.argos.so/entities/john-kerry"
            }],
            "members": [{
                "title": "On Tour of Mideast, Kerry Says Iran Might Play Role in Syria Peace Talks",
                "url": "http://www.nytimes.com/2014/01/06/world/middleeast/kerry-iran-syria.html",
                "id": 1,
                "created_at": "2014-02-06T20:55:54.597459"
            }]
        }
    ]
