Articles
------

**Get a single article**::

    GET /articles/:id

Example request::

    curl -H "Accept: application/json" http://localhost:5000/articles/1

Example response

.. code-block:: json

    {
        "id": 1,
        "url": "/articles/1",
        "title": "Kerry leads Syrian peace talks",
        "image": "https://s3.amazonaws.com/argos/189751513.jpg",
        "ext_url": "http://www.nytimes.com/2014/01/06/world/middleeast/kerry-iran-syria.html",
        "updated_at": "2014-02-07T23:42:15.581374",
        "created_at": "2014-02-06T20:55:54.597459",
        "authors": [{
            "id": 1,
            "url": "/authors/1"
        }],
        "events": [{
            "id": 1,
            "url": "/events/1"
        }],
        "source": {
            "id": 1,
            "url": "/sources/1",
            "name": "The Times"
        }
    }
