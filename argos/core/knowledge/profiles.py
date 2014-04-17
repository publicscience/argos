"""
Profiles
========

Constructs a specific "data profile" for
a resource (concept) based on its ontological type.
"""

from argos.core.knowledge import _quote, _get_results, types_for_uri, name_for_uri, image_for_uri, services

def get_profile(uri):
    types = types_for_uri(uri)

    if 'http://dbpedia.org/ontology/Company' in types:
        profile = get_company_profile(uri)
        profile['type'] = 'company'
        return profile
    elif 'http://dbpedia.org/ontology/Place' in types:
        profile = get_place_profile(uri, types)
        profile['type'] = 'place'
        return profile

def get_company_profile(uri):
    """
    Example return value::

        {'assets': 'US$ 93.80 billion',
         'contributions': {
                'democrat': '747341',
                'lobbying': '15800000',
                'republican': '483817',
                'total': '1461482',
                'year': '2014'
         },
         'employees': '53861',
         'income': 'US$ 10.74 billion',
         'name': 'Google',
         'revenue': 'US$ 50.18 billion',
         'subsidiaries': {
            'http://dbpedia.org/resource/AdMob': 'AdMob',
            'http://dbpedia.org/resource/DoubleClick': 'DoubleClick',
            'http://dbpedia.org/resource/Motorola_Mobility': 'Motorola Mobility',
            'http://dbpedia.org/resource/On2_Technologies': 'On2 Technologies',
            'http://dbpedia.org/resource/Picnik': 'Picnik',
            'http://dbpedia.org/resource/YouTube': 'YouTube',
            'http://dbpedia.org/resource/Zagat': 'Zagat'
         },
         'symbol': 'GOOG'}
     """

    # MISSING
    # Perhaps need to be using dbpedia live for this.
    #dbo:parentCompany ?children;
    #dbo:owningCompany ?owns;
    #dbo:board ?board;
    #dbo:developer ?products;
    #dbo:manufacturer ?moreproducts .

    uri = _quote(uri)

    query = '''
        SELECT *
        WHERE {{
            <{uri}> rdfs:label ?name;
                    dbo:subsidiary ?subsidiaries;
                    dbo:numberOfEmployees ?employees;
                    dbp:symbol ?symbol;
                    dbp:assets ?assets;
                    dbp:netIncome ?income;
                    dbp:revenue ?revenue .
        }}
    '''.format(uri=uri)

    results = _get_results(query)

    # Get the names for each subsidiary.
    subsidiaries = {}
    for subsidiary in [result['subsidiaries'] for result in results]:
        # This should be combined into a single query.
        subsidiaries[subsidiary] = {'name': name_for_uri(subsidiary), 'image': image_for_uri(subsidiary)}

    profile = None
    if results:
        profile = results[0]
        profile['subsidiaries'] = subsidiaries

        # For now just using the first result,
        # but it is possible that multiple organizations are returned.
        os_data = services.opensecrets.organizations(profile['name'])
        profile['contributions'] = os_data[0]['contributions']

    return profile

def get_place_profile(uri, types):
    """
    Example return value::

        {'areaKm': '603628',
         'areaSqMi': '233090',
         'capital': 'http://dbpedia.org/resource/Kiev',
         'latitude': '49.0',
         'leaders': {'http://dbpedia.org/resource/Mykola_Azarov': 'Mykola Azarov',
          'http://dbpedia.org/resource/Viktor_Yanukovych': 'Viktor Yanukovych',
          'http://dbpedia.org/resource/Volodymyr_Rybak': 'Volodymyr Rybak'},
         'longitude': '32.0',
         'population': '44854065',
         'populationDensityKm': '77',
         'populationDensitySqMi': '199',
         'populationYear': '2012'}
    """
    uri = _quote(uri)

    query = '''
        SELECT *
        WHERE {{
            <{uri}> geo:lat ?latitude;
                    geo:long ?longitude .
            OPTIONAL {{ <{uri}> dbp:capital ?capital . }}
            OPTIONAL {{ <{uri}> dbp:leaderName ?leaders . }}
            OPTIONAL {{
                <{uri}> dbp:areaKm ?areaKm;
                        dbp:areaSqMi ?areaSqMi . }}
            OPTIONAL {{
                <{uri}> dbp:populationEstimate ?population;
                        dbp:populationEstimateYear ?populationYear . }}
            OPTIONAL {{
                <{uri}> dbp:populationDensityKm ?populationDensityKm;
                        dbp:populationDensitySqMi ?populationDensitySqMi . }}
        }}
    '''.format(uri=uri)

    results = _get_results(query)

    # Get the names for each leader.
    leaders = {}
    for leader in [result['leaders'] for result in results if result.get('leaders', None)]:
        leaders[leader] = name_for_uri(leader)

    profile = None
    if results:
        profile = results[0]
        profile['leaders'] = leaders

        distance = 1000
        if 'http://dbpedia.org/ontology/Country' in types:
            distance = 4000
        elif 'http://dbpedia.org/ontology/Region' in types:
            distance = 2000
        # etc

        profile['photos'] = services.instagram.photos_at_location(profile['latitude'], profile['longitude'], distance=distance)


    return profile
