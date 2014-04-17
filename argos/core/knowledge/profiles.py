"""
Profiles
========

Constructs a specific "data profile" for
a resource (concept) based on its ontological type.
"""

from argos.core.knowledge import _quote, _get_results, types_for_uri, name_for_uri, services

def get_profile(uri):
    types = types_for_uri(uri)

    if 'http://dbpedia.org/ontology/Company' in types:
        profile = get_company_profile(uri)
        profile['type'] = 'company'
        return profile
    elif 'http://dbpedia.org/ontology/Place' in types:
        profile = get_place_profile(uri)
        profile['type'] = 'place'
        return profile

def get_company_profile(uri):
    """
    Example return value::

        {'assets': 'US$ 93.80 billion',
         'contributions': [{
            'contributions': {
                'democrat': '747341',
                'lobbying': '15800000',
                'republican': '483817',
                'total': '1461482'
            },
           'year': '2014'}],
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
        subsidiaries[subsidiary] = name_for_uri(subsidiary)

    profile = results[0]
    profile['subsidiaries'] = subsidiaries

    contributions = services.opensecrets.organizations(profile['name'])
    profile['contributions'] = contributions

    return profile

def get_place_profile(uri):
    uri = _quote(uri)

    query = '''
        SELECT *
        WHERE {{
            <{uri}> dbp:capital ?capital;
                    dbp:areaKm ?areaKm;
                    dbp:areaSqMi ?areaSqMi;
                    dbp:imageFlag ?flag;
                    dbp:populationEstimate ?population;
                    dbp:populationEstimateYear ?populationYear;
                    dbp:populationDensityKm ?populationDensityKm;
                    dbp:populationDensitySqMi ?populationDensitySqMi;
                    dbo:leaderName ?leaders;
                    geo:lat ?latitude;
                    geo:long ?longitude .
        }}
    '''.format(uri=uri)

    results = _get_results(query)

    # Get the names for each leader.
    leaders = {}
    for leader in [result['leaders'] for result in results]:
        leaders[leader] = name_for_uri(leader)

    profile = results[0]
    profile['leaders'] = leaders

    return profile
