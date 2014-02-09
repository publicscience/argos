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

    [{
        "id": 1,
        "image": "https://s3.amazonaws.com/argos/12479514.jpg",
        "name": "Isaac Clarke",
        "updated_at": "2014-02-07T23:42:15.581374",
        "created_at": "2014-02-06T20:55:54.597459"
    }]

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
