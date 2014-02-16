Authors
------

**Get a single author**::

    GET /authors/:id

Example response

.. code-block:: json

    {
        "id": 1,
        "url": "/authors/1",
        "name": "Bob Woodward",
        "articles": [{
            "url": "/articles/1"
        }]
    }
