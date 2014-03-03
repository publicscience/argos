Search
------

**Search events, stories, and entities**::

    GET /search

Parameters

+---------------+--------+----------------------------------+
| Name          | Type   | Description                      |
+===============+========+==================================+
| query         | str    | The query to search for.         |
+---------------+--------+----------------------------------+

Example response

.. code-block:: json

    {
        "results":  [
                        {
                            "id": 1,
                            "url": "/events/1",
                            "type": "event",
                            "title": "Kerry leads Syrian peace talks",
                            "image": "https://s3.amazonaws.com/argos/189751513.jpg",
                            "summary": "Secretary of State John Kerry said on Sunday that Iran might play...",
                            "updated_at": "2014-02-07T23:42:15.581374",
                            "created_at": "2014-02-06T20:55:54.597459"
                        },
                        {
                            "id": 1,
                            "url": "/stories/1",
                            "type": "story",
                            "title": "Syrian civil war",
                            "image": "https://s3.amazonaws.com/argos/237383249.jpg",
                            "summary": "Armed uprising in Syria between President Assad and the Muslim Brotherhood...",
                            "updated_at": "2014-02-07T23:42:15.581374",
                            "created_at": "2014-02-06T20:55:54.597459"
                        }
                    ],
        "count":    2
    }
