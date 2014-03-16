Concepts
------

**Get a single concept**::

    GET /concepts/:slug

Example response

.. code-block:: json

    {
        "name": "John Kerry",
        "names": ["John Kerry", "J. Kerry", "Secretary Kerry"],
        "slug": "john-kerry",
        "summary": "John Kerry is the current US Secretary of State..."
        "image": "https://s3.amazonaws.com/argos/12948741.jpg",
        "url": "/entities/john-kerry",
        "updated_at": "2014-02-07T23:42:15.581374",
        "stories": [{
            "url": "/stories/1",
            "relatedness": "0.24"
        }]
    }
