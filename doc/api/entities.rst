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
        "updated_at": "2014-02-07T23:42:15.581374",
        "stories": [{
            "url": "/stories/1"
        }]
    }
