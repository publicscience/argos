Stories
-------

**Get all stories (paginated)**::

    GET /stories

Parameters

+---------------+--------+----------------------------------+
| Name          | Type   | Description                      |
+===============+========+==================================+
| page          | int    | The page of stories to fetch.    |
+---------------+--------+----------------------------------+

Example response

.. code-block:: json

    [
        {
            "id": 1,
            "url": "/stories/1",
            "title": "Syrian civil war",
            "image": "https://s3.amazonaws.com/argos/237383249.jpg",
            "images": ["https://s3.amazonaws.com/argos/2487149.jpg", "https://s3.amazonaws.com/argos/1248979.jpg"],
            "summary": "Armed uprising in Syria between President Assad and the Muslim Brotherhood...",
            "updated_at": "2014-02-07T23:42:15.581374",
            "created_at": "2014-02-06T20:55:54.597459",
            "entities": [{
                "url": "/entities/muslim-brotherhood"
            }],
            "mentions": [{
                "name": "The Muslim Brotherhood",
                "slug": "muslim-brotherhood"
            }],
            "events": [{
                "url": "/events/1"
            }],
            "watchers": [{
                "url": "/users/1"
            }]
        }
    ]

-----

**Get a single story**::

    GET /stories/:id

Example response

.. code-block:: json

    {
        "id": 1,
        "url": "/stories/1",
        "title": "Syrian civil war",
        "image": "https://s3.amazonaws.com/argos/237383249.jpg",
        "images": ["https://s3.amazonaws.com/argos/2487149.jpg", "https://s3.amazonaws.com/argos/1248979.jpg"],
        "summary": "Armed uprising in Syria between President Assad and the Muslim Brotherhood...",
        "updated_at": "2014-02-07T23:42:15.581374",
        "created_at": "2014-02-06T20:55:54.597459",
        "entities": [{
            "url": "/entities/muslim-brotherhood"
        }],
        "mentions": [{
            "name": "The Muslim Brotherhood",
            "slug": "muslim-brotherhood"
        }],
        "events": [{
            "url": "/events/1"
        }],
        "watchers": [{
            "url": "/users/1"
        }]
    }

-----

**Get a story's watchers**::

    GET /stories/:id/watchers

Example response

.. code-block:: json

    [
        {
            "id": 1,
            "image": "https://s3.amazonaws.com/argos/12479514.jpg",
            "name": "Isaac Clarke",
            "updated_at": "2014-02-07T23:42:15.581374",
            "created_at": "2014-02-06T20:55:54.597459"
        }
    ]

-----

**Watch a story with the authenticated user**::

    POST /stories/:id/watchers

Example response

.. code-block:: json

    201

-----

**Stop watching a story with the authenticated user**::

    DELETE /stories/:id/watchers

Example response

.. code-block:: json

    204
