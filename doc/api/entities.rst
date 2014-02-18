Entities
------

**Get a single entity**::

    GET /entities/:slug

Example response

.. code-block:: json

    {
        "name": "John Kerry",
        "slug": "john-kerry",
        "url": "/entities/john-kerry",
        "stories": [{
            "url": "/stories/1"
        }]
    }
