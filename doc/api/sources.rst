Sources
------

**Get a single source**::

    GET /sources/:id

Example response

.. code-block:: json

    {
        "id": 1,
        "url": "/sources/1",
        "name": "New York Times Home Page",
        "ext_url": "http://www.nytimes.com/services/xml/rss/nyt/HomePage.xml"
        "articles": [{
            "url": "/articles/1"
        }]
    }
