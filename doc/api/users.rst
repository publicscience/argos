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

    {
        "id": 1,
        "image": "https://s3.amazonaws.com/argos/12479514.jpg",
        "name": "Isaac Clarke",
        "updated_at": "2014-02-07T23:42:15.581374",
        "created_at": "2014-02-06T20:55:54.597459"
    }

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
            "summary": "Armed uprising in Syria between President Assad and the Muslim Brotherhood...",
            "updated_at": "2014-02-07T23:42:15.581374",
            "created_at": "2014-02-06T20:55:54.597459",
            "entities": [{
                "url": "/entities/muslim-brotherhood"
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

    [
        {
            "id": 1,
            "url": "/stories/1",
            "title": "Syrian civil war",
            "image": "https://s3.amazonaws.com/argos/237383249.jpg",
            "summary": "Armed uprising in Syria between President Assad and the Muslim Brotherhood...",
            "updated_at": "2014-02-07T23:42:15.581374",
            "created_at": "2014-02-06T20:55:54.597459",
            "entities": [{
                "url": "/entities/muslim-brotherhood"
            }],
            "events": [{
                "url": "/events/1"
            }],
            "watchers": [{
                "url": "/users/1"
            }]
        }
    ]
