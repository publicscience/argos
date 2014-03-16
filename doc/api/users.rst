Users
-----

**Get all users (paginated)**::

    GET /users

Parameters

+---------------+--------+----------------------------------+
| Name          | Type   | Description                      |
+===============+========+==================================+
| page          | int    | The page of users to fetch.      |
+---------------+--------+----------------------------------+

Example response

.. code-block:: json

    {
        "results": [{
            "id": 1,
            "image": "https://s3.amazonaws.com/argos/12479514.jpg",
            "name": "Isaac Clarke",
            "updated_at": "2014-02-07T23:42:15.581374",
            "created_at": "2014-02-06T20:55:54.597459"
        }],
        "pagination": {
            "page": 1,
            "per_page": 20,
            "total_count": 240
        }
    }

-----

**Get a single user**::

    GET /users/:id

Example response

.. code-block:: json

    {
        "id": 1,
        "image": "https://s3.amazonaws.com/argos/12479514.jpg",
        "name": "Isaac Clarke",
        "updated_at": "2014-02-07T23:42:15.581374",
        "created_at": "2014-02-06T20:55:54.597459"
    }

-----

**Get the currently authenticated user**::

    GET /user

Example response

.. code-block:: json

    {
        "id": 1,
        "image": "https://s3.amazonaws.com/argos/12479514.jpg",
        "name": "Isaac Clarke",
        "updated_at": "2014-02-07T23:42:15.581374",
        "created_at": "2014-02-06T20:55:54.597459"
    }

-----

**Update the currently authenticated user**::

    PATCH /user

Example response

.. code-block:: json

    204

-----

**Get the currently authenticated user's watched stories**::

    GET /user/watching

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
            "concepts": [{
                "url": "/concepts/muslim-brotherhood",
                "score": "0.67"
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

**Add a story to the currently authenticated user watched stories**::

    POST /user/watching

Parameters

+---------------+--------+----------------------------------+
| Name          | Type   | Description                      |
+===============+========+==================================+
| story_id      | int    | The id of the story to watch.    |
+---------------+--------+----------------------------------+

Example response

.. code-block:: json

    201

-----

**Add a story to the currently authenticated user watched stories**::

    DELETE /user/watching

Parameters

+---------------+--------+---------------------------------------+
| Name          | Type   | Description                           |
+===============+========+=======================================+
| story_id      | int    | The id of the story to stop watching. |
+---------------+--------+---------------------------------------+

Example response

for `/user/watching?story_id=1`

.. code-block:: json

    204

-----

**Check if the user is watching a given story**::

    GET /user/watching/:id

Example responses

If user is watching:

.. code-block:: json

    204

If user is not watching:

.. code-block:: json

    404

-----

**Get the currently authenticated user's bookmarked events**::

    GET /user/bookmarked

Example response

.. code-block:: json

    [
        {
            "id": 1,
            "url": "/events/1",
            "title": "Kerry leads Syrian peace talks",
            "image": "https://s3.amazonaws.com/argos/189751513.jpg",
            "images": ["https://s3.amazonaws.com/argos/2487149.jpg", "https://s3.amazonaws.com/argos/1248979.jpg"],
            "summary": "Secretary of State John Kerry said on Sunday that Iran might play...",
            "score": 71283,
            "updated_at": "2014-02-07T23:42:15.581374",
            "created_at": "2014-02-06T20:55:54.597459",
            "concepts": [{
                "url": "/concepts/john-kerry",
                "score": "0.67"
            }],
            "mentions": [{
                "name": "John Kerry",
                "slug": "john-kerry"
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

**Add a event to the currently authenticated user bookmarked events**::

    POST /user/bookmarked

Parameters

+---------------+--------+----------------------------------+
| Name          | Type   | Description                      |
+===============+========+==================================+
| event_id      | int    | The id of the event to bookmark. |
+---------------+--------+----------------------------------+

Example response

.. code-block:: json

    201

**Add a event to the currently authenticated user bookmarked events**::

    DELETE /user/bookmarked

Parameters

+---------------+--------+---------------------------------------+
| Name          | Type   | Description                           |
+===============+========+=======================================+
| event_id      | int    | The id of the event to unbookmark.    |
+---------------+--------+---------------------------------------+

Example response

for `/user/bookmarked?event_id=1`

.. code-block:: json

    204

-----

**Check if the user has a particular event bookmarked**::

    GET /user/bookmarked/:id

Example responses

If user has the event bookmarked:

.. code-block:: json

    204

If user does not have the event bookmarked:

.. code-block:: json

    404

