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
        "commonness": "11847.0",
        "url": "/entities/john-kerry",
        "updated_at": "2014-02-07T23:42:15.581374",
        "profile": {},
        "stories": [{
            "id": 1,
            "url": "/stories/1",
            "relatedness": "0.24"
        }]
    }


Profile examples:

Place

.. code-block:: json

    {
        ...
        "profile": {
            "type": "place",
            "areaKm": "603628",
            "areaSqMi": "233090",
            "capital": "http://dbpedia.org/resource/Kiev",
            "latitude": "49.0",
            "longitude": "32.0",
            "leaders": {
                "http://dbpedia.org/resource/Mykola_Azarov": "Mykola Azarov",
                "http://dbpedia.org/resource/Viktor_Yanukovych": "Viktor Yanukovych",
                "http://dbpedia.org/resource/Volodymyr_Rybak": "Volodymyr Rybak"
            },
            "population": "44854065",
            "populationDensityKm": "77",
            "populationDensitySqMi": "199",
            "populationYear": "2012",
            "photos": ["http://foo.com/photo1.jpg", "http://foo.com/photo2.jpg"]
        }
        ...
    }

Company

.. code-block:: json

    {
        ...
        "profile": {
            "type": "company",
            "assets": "US$ 93.80 billion",
            "contributions": [{
                "direct_amount": "0",
                "direct_count": "0",
                "employee_amount": "1602978.00",
                "employee_count": "2274",
                "id": "4148b26f6f1c437cb50ea9ca4699417a",
                "name": "Barack Obama (D)",
                "party": "D",
                "state": "",
                "total_amount": "1602978.00",
                "total_count": "2274"
            }],
            "party_contributions": {
                "Democrats": ["5157", "6166411.11"],
                "Other": ["831", "2022397.43"],
                "Republicans": ["1114", "1998822.25"]
            },
            "employees": "53861",
            "income": "US$ 10.74 billion",
            "name": "Google",
            "revenue": "US$ 50.18 billion",
            "subsidiaries": [{
                "http://dbpedia.org/resource/YouTube": {
                    "image": "http://upload.wikimedia.org/wikipedia/commons/e/e8/Logo_Youtube.svg",
                    "name": "YouTube"
                }
            }],
            "symbol": "GOOG"
        }
        ...
    }
