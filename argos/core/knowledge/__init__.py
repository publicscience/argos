"""
Knowledge
==============

Collects information about resources/entities.

Currently uses DBpedia RDF dumps (processed by `argos.core.digester.knowledge`),
as served by Apache Jena's Fuseki. The main functionality here is interfacing
with the Fuseki server through HTTP SPARQL requests.

The Fuseki server returns JSON responses.

For instance, a request with the SPARQL query::

    curl -i -X POST -d "query=SELECT ?p ?o WHERE { <http://dbpedia.org/resource/The_Muslim_Brotherhood> ?p ?o}" localhost:3030/knowledge/query

Would return the response::

    HTTP/1.1 200 OK
    Fuseki-Request-ID: 8
    Access-Control-Allow-Origin: *
    Server: Fuseki (1.0.1)
    Cache-Control: no-cache
    Pragma: no-cache
    Content-Type: application/sparql-results+json; charset=utf-8
    Transfer-Encoding: chunked

    {
      "head": {
        "vars": [ "p" , "o" ]
      } ,
      "results": {
        "bindings": [
          {
            "p": { "type": "uri" , "value": "http://www.w3.org/2000/01/rdf-schema#label" } ,
            "o": { "type": "literal" , "xml:lang": "en" , "value": "The Muslim Brotherhood" }
          } ,
          {
            "p": { "type": "uri" , "value": "http://dbpedia.org/ontology/wikiPageRedirects" } ,
            "o": { "type": "uri" , "value": "http://dbpedia.org/resource/Muslim_Brotherhood" }
          }
        ]
      }
    }


NOTE:
=====

DBpedia dumps can have double quotes in their URIs, so
they are not valid IRIs, and as such, they are invalid Fuseki SPARQL.
I've read elsewhere that if you percent escape them (i.e. make them %22),
they should work. But they don't.
So for now they are just being removed.

warning::
    if `fallback=True`, then if a uri is not found for a name,
    DBpedia live will be queried. This is ok for now, but if usage
    becomes particularly heavy, some other arrangement should be used
    (e.g. hosting our own DBpedia live database).
"""

from urllib import request, error
from urllib.parse import urlencode
import json

from argos.conf import APP

from argos.util.logger import logger
logger = logger(__name__)

# Define some commonly used prefixed up front.
# This are sent as part of each query.
PREFIXES = """
PREFIX rdfs: <http://www.w3.org/2000/01/rdf-schema#>
PREFIX rdf: <http://www.w3.org/1999/02/22-rdf-syntax-ns#>
PREFIX xsd: <http://www.w3.org/2001/XMLSchema#>
PREFIX foaf: <http://xmlns.com/foaf/0.1/>
PREFIX dbo: <http://dbpedia.org/ontology/>
PREFIX dbp: <http://dbpedia.org/property/>
PREFIX owl: <http://www.w3.org/2002/07/owl#>
PREFIX dc: <http://purl.org/dc/elements/1.1/>
PREFIX geo: <http://www.w3.org/2003/01/geo/wgs84_pos#>
"""

def uri_for_name(name, fallback=False):
    """
    Returns the canonical URI for a given entity name.
    This will also match common mispellings or alternate spellings.*
    If none is found, None is returned.

    Example::

        >>> uri_for_name("United States Secretary of State")
        'http://dbpedia.org/resource/United_States_Secretary_of_State'
        >>> uri_for_name("US Secretary of State")
        'http://dbpedia.org/resource/United_States_Secretary_of_State'

    *Note that a potential problem here is that, with the way DBpedia/Wikipedia
    are setup, closely related entities which may not merit a page of their own,
    but are in fact different, may still turn up as an alias (i.e. a redirect) for an entity.
    For example, an alias for 'John Kerry' is 'Peggy Kerry', who is his sister. She should
    be her own entity, but in the dataset, there is a Wikipedia redirect from her to him.

    warning::
        requires the `labels` dbpedia dataset.
    """

    # Note: double braces are parsed down to single braces when using `str.format()`.
    base_query = '''
        SELECT ?uri
        WHERE {{
            {{ ?alias_uri rdfs:label "{0}"@en; dbo:wikiPageRedirects ?uri . }}
            UNION
            {{ ?uri rdfs:label "{0}"@en
                FILTER NOT EXISTS {{  ?uri dbo:wikiPageRedirects ?nil }}
            }}
        }}
    '''
    query = _build_query(base_query, name)
    results = _get_results(query)
    if results:
        return results[0].get('uri')
    elif fallback:
        results = _get_live_results(query)
        if results:
            return results[-1].get('uri')
    return None

def name_for_uri(uri):
    """
    Returns a name for a given uri.
    If none is found, None is returned.

    warning::
        requires the `labels` dbpedia dataset.
    """
    uri = _quote(uri)
    query = 'SELECT ?name WHERE {{ <{0}> rdfs:label ?name }}'.format(uri)
    results = _get_results(query)
    if results:
        return results[0].get('name')
    return None

def image_for_name(name, fallback=False):
    """
    Returns an image URL for a given entity name.
    If none is found, None is returned.

    If `fallback=True`, will fallback to DBpedia live
    for an image.

    If you know there is no URI for the specified name,
    i.e. from having separately called `uri_for_name`,
    you can specify `no_uri=True`, and querying for the
    URI will be skipped. Note that this overrides the user
    value for `fallback` and sets it to `True`.

    Example::

        >>> image_for_name("Star Trek")
        'http://upload.wikimedia.org/wikipedia/commons/7/7e/StarTrek_Logo_2007.JPG'

    warning::
        requires the `images` dbpedia dataset.
    """

    uri = uri_for_name(name, fallback=fallback)
    return image_for_uri(uri, fallback=fallback)

def image_for_uri(uri, fallback=False):
    """
    Returns an image URL for a given entity URI.
    If none is found, None is returned.

    warning::
        requires the `images` dbpedia dataset.
    """
    uri = _quote(uri)
    query = 'SELECT ?image_url WHERE {{ <{0}> foaf:depiction ?image_url }}'.format(uri)
    results = _get_results(query)
    if results:
        return results[0].get('image_url')
    elif fallback:
        results = _get_live_results(query)
        if results:
            return results[-1].get('image_url')
    return None

def coordinates_for_name(name, fallback=False):
    """
    Returns a set of coordinates for a given entity name.
    If none is found, None is returned.

    Example::

        >>> coordinates_for_name("Beijing")
        {'lat': '39.90638888888889', 'long': '116.37972222222223'}

    warning::
        requires the `geo_coordinates` dbpedia dataset.
    """
    uri = uri_for_name(name, fallback=fallback)
    return coordinates_for_uri(uri, fallback=fallback)

def coordinates_for_uri(uri, fallback=False):
    """
    Returns a set of coordinates for a given entity URI.
    If none is found, None is returned.

    warning::
        requires the `geo_coordinates` dbpedia dataset.
    """
    uri = _quote(uri)
    query = 'SELECT ?lat ?long WHERE {{ <{0}> geo:lat ?lat; geo:long ?long }}'.format(uri)
    results = _get_results(query)
    if results:
        return results[0]
    elif fallback:
        results = _get_live_results(query)
        if results:
            return results[-1]
    return None

def summary_for_name(name, short=False, fallback=False):
    """
    Returns a summary for a given entity name.
    If none is found, None is returned.

    Optionally specify `short=True` to get a
    shorter summary.

    Example::

        >>> summary_for_name("Beijing", short=True)
        "Beijing, sometimes romanized as Peking, is the capital of the People's Republic of China and one of the most populous cities in the world. The population as of 2012 was 20,693,000. The metropolis, located in northern China, is governed as a direct-controlled municipality under the national government, with 14 urban and suburban districts and two rural counties. Beijing Municipality is surrounded by Hebei Province with the exception of neighboring Tianjin Municipality to the southeast."

    warning::
        requires the `long_abstracts` dbpedia dataset.
        requires the `short_abstracts` dbpedia dataset.
    """
    uri = uri_for_name(name, fallback=fallback)
    return summary_for_uri(uri, short=short, fallback=fallback)

def summary_for_uri(uri, short=False, fallback=False):
    """
    Returns a summary for a given entity URI.
    If none is found, None is returned.

    Optionally specify `short=True` to get a
    shorter summary.

    warning::
        requires the `long_abstracts` dbpedia dataset.
        requires the `short_abstracts` dbpedia dataset.
    """
    uri = _quote(uri)
    predicate = 'rdfs:comment' if short else 'dbo:abstract'
    query = 'SELECT ?summary WHERE {{ <{0}> {1} ?summary }}'.format(uri, predicate)
    results = _get_results(query)
    if results:
        return results[0].get('summary')
    elif fallback:
        results = _get_live_results(query)
        if results:
            return results[-1].get('summary')
    return None

def aliases_for_name(name, fallback=False):
    """
    Returns a list of alias URIs for a given entity name.

    Example::

        >>> aliases_for_name("United States Secretary of State")
        ['http://dbpedia.org/resource/US_Secretary_Of_State',
         'http://dbpedia.org/resource/Secretary_of_State_of_the_United_States',
         'http://dbpedia.org/resource/US_Secretary_of_State', ...]

    warning::
        requires the `redirects` dbpedia dataset.
    """

    uri = uri_for_name(name, fallback=fallback)
    return aliases_for_uri(uri, fallback=fallback)

def aliases_for_uri(uri, fallback=False):
    """
    Returns a list of alias URIs for a given entity URI.

    warning::
        requires the `redirects` dbpedia dataset.
    """
    uri = _quote(uri)
    query = 'SELECT ?alias_uri WHERE {{ ?alias_uri dbo:wikiPageRedirects <{0}> }}'.format(uri)
    results = _get_results(query)
    if results:
        return [d['alias_uri'] for d in results]
    elif fallback:
        return [d['alias_uri'] for d in _get_live_results(query)]
    return None

def types_for_uri(uri, fallback=False):
    """
    Returns a list of types for a given entity URI.

    Example::

        >>> types_for_uri('http://dbpedia.org/resource/Google')
        ['http://www.w3.org/2002/07/owl#Thing',
         'http://dbpedia.org/ontology/Agent',
         'http://dbpedia.org/ontology/Organisation',
         'http://schema.org/Organization',
         'http://dbpedia.org/ontology/Company']

    warning::
        requires the `instance_types` dbpedia dataset.
    """
    uri = _quote(uri)
    query = 'SELECT ?type WHERE {{ <{0}> rdf:type ?type }}'.format(uri)
    results = _get_results(query)
    if results:
        return [d['type'] for d in results]
    elif fallback:
        return [d['type'] for d in _get_live_results(query)]
    return []

def types_for_name(name, fallback=False):
    """
    Returns a list of types for a given entity name.

    warning::
        requires the `instance_types` dbpedia dataset.
    """
    uri = uri_for_name(name, fallback=fallback)
    return types_for_uri(uri, fallback=fallback)

def pagelinks_for_uri(uri, fallback=False):
    """
    Gets the number of pagelinks *to* a URI.

    warning::
        requires the `page_links` dbpedia dataset.
    """
    uri = _quote(uri)
    query = 'SELECT ?from WHERE {{ ?from dbo:wikiPageWikiLink <{0}> }}'.format(uri)
    results = _get_results(query)
    if results:
        return [d['from'] for d in results]
    elif fallback:
        return [d['from'] for d in _get_live_results(query)]
    return []

def pagelinks_for_name(name, fallback=False):
    """
    Gets the number of pagelinks *to* a given entity name.

    warning::
        requires the `page_links` dbpedia dataset.
    """
    uri = uri_for_name(name, fallback=fallback)
    return pagelinks_for_uri(uri, fallback=fallback)

def commonness_for_uri(uri, fallback=False):
    """
    Calculates a commonness score for a URI.

    warning::
        requires the `page_links` dbpedia dataset.
    """
    pagelinks = pagelinks_for_uri(uri, fallback=fallback)
    return len(pagelinks)

def commonness_for_name(name, fallback=False):
    """
    Calculates a commonness score for a given entity name.

    warning::
        requires the `page_links` dbpedia dataset.
    """
    pagelinks = pagelinks_for_name(name, fallback=fallback)
    return len(pagelinks)

def knowledge_for(uri, fallback=False):
    """
    A convenience method for getting necessary information
    for a given name or uri.

    Either a `uri` or `name` must be specified. If both are specified,
    the `uri` is given priority.

    If a `uri` is specified, you can optionally specify `fallback=True`
    which means Wikipedia will be used in the event that some of the
    information can't be found in the existing knowledge database.

    If you specify a `name`, the `fallback` value is ignored,
    and Wikipedia is automatically used for gathering the information.
    """

    results = {}
    uri = _quote(uri)
    results['summary'] = summary_for_uri(uri, short=False, fallback=fallback)
    results['image'] = image_for_uri(uri, fallback=fallback)
    results['name'] = name_for_uri(uri)
    return results


def _query(query):
    data = '{0} {1}'.format(PREFIXES, query).encode('utf-8')
    req = request.Request('http://{host}:3030/knowledge/query'.format(host=APP['KNOWLEDGE_HOST']),
            headers={
                'Accept': 'application/sparql-results+json',
                'Content-Type': 'application/sparql-query'
            },
            data=data)
    try:
        res = request.urlopen(req)
    except error.HTTPError as e:
        logger.exception('Error with query: {0}'.format(query))
        raise e
    if res.status != 200:
        raise Exception('Response error, status was not 200')
    else:
        content = res.read()
        return json.loads(content.decode('utf-8'))
    return None

def _prepare_results(data):
    """
    Go from this::

        {
          "head": {
            "vars": [ "p" , "o" ]
          } ,
          "results": {
            "bindings": [
              {
                "p": { "type": "uri" , "value": "http://www.w3.org/2000/01/rdf-schema#label" } ,
                "o": { "type": "literal" , "xml:lang": "en" , "value": "The Muslim Brotherhood" }
              } ,
              {
                "p": { "type": "uri" , "value": "http://dbpedia.org/ontology/wikiPageRedirects" } ,
                "o": { "type": "uri" , "value": "http://dbpedia.org/resource/Muslim_Brotherhood" }
              }
            ]
          }
        }

    To this::

        [
          {
            'p': 'http://www.w3.org/2000/01/rdf-schema#label',
            'o': 'The Muslim Brotherhood'
          },
          {
            'p': 'http://dbpedia.org/ontology/wikiPageRedirects',
            'o': 'http://dbpedia.org/resource/Muslim_Brotherhood'
          }
        ]
    """
    bindings = data['results']['bindings']
    results = []
    for binding in bindings:
        results.append({k: v['value'] for k, v in binding.items()})
    return results

def _get_results(query):
    """
    Convenience method for making a query
    and getting formatted results.
    """
    data = _query(query)
    return _prepare_results(data)

def _build_query(base_query, *args):
    """
    Formats a query with arguments, sanitizing
    the arguments first.
    """
    sanitized_args = [_sanitize(arg) for arg in args]
    return base_query.format(*sanitized_args)

def _sanitize(text):
    """
    Properly escape SPARQL strings.
    """
    mappings = [
		("\\", "\\\\"),
        ("\t", "\\t"),
		("\n", "\\n"),
		("\r", "\\r"),
		("\b", "\\b"),
		("\f", "\\f"),
		("\"", "\\\""),
        ("'", "\\'"),
    ]
    for mapping in mappings:
        text = text.replace(mapping[0], mapping[1])
    return text

def _quote(text):
    """
    Properly quote URIs.
    """
    if text:
        mappings = [
            ("\"", "%22"),
        ]
        for mapping in mappings:
            text = text.replace(mapping[0], mapping[1])
    return text

def _get_live_results(query):
    """
    Convenience method for making a query
    and getting formatted results from the
    DBpedia live endpoint.
    """
    data = _query_live(query)
    return _prepare_results(data)

def _query_live(query):
    """
    Query the DBpedia live endpoint. We should be respectful of
    using this endpoint too much; if we find that is the case,
    we should setup our own synchronized DBpedia live endpoint.
    """
    data = {'query': '{0} {1}'.format(PREFIXES, query).replace('\n', ' ')}
    endpoint = 'http://dbpedia-live.openlinksw.com/sparql'
    url = '{endpoint}?{query}'.format(
            endpoint=endpoint,
            query=urlencode(data)
          )
    req = request.Request(url,
            headers={
                'Accept': 'application/json',
                'Content-Type': 'application/sparql-query'
            })
    try:
        res = request.urlopen(req)
    except error.HTTPError as e:
        logger.exception('Error with query: {0}\n\nError: {1}'.format(query, e.read()))
        raise e
    if res.status != 200:
        raise Exception('Response error, status was not 200')
    else:
        content = res.read()
        return json.loads(content.decode('utf-8'))
    return None


from argos.core.knowledge import profiles
