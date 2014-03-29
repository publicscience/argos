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
"""

from urllib import request
import json

from argos.conf import APP

# Define some commonly used prefixed up front.
# This are sent as part of each query.
PREFIXES = """
PREFIX rdfs: <http://www.w3.org/2000/01/rdf-schema#>
PREFIX rdf: <http://www.w3.org/1999/02/22-rdf-syntax-ns#>
PREFIX xsd: <http://www.w3.org/2001/XMLSchema#>
PREFIX foaf: <http://xmlns.com/foaf/0.1/>
PREFIX dbo: <http://dbpedia.org/ontology/>
PREFIX owl: <http://www.w3.org/2002/07/owl#>
PREFIX dc: <http://purl.org/dc/elements/1.1/>
PREFIX geo: <http://www.w3.org/2003/01/geo/wgs84_pos#>
"""

def uri_for_name(name):
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
    """

    # Note: double braces are parsed down to single braces when using `str.format()`.
    base_query = '''
        SELECT ?uri
        WHERE {{
            {{ ?alias_uri rdfs:label "{0}"@en; dbo:wikiPageRedirects ?uri . }}
            UNION
            {{ ?uri rdfs:label "{0}"@en
                NOT EXISTS {{  ?uri dbo:wikiPageRedirects ?nil }}
            }}
        }}
    '''
    query = _build_query(base_query, name)
    data = _query(query)
    results = _prepare_results(data)
    if results:
        return results[0].get('uri')
    return None

def name_for_uri(uri):
    """
    Returns a name for a given uri.
    If none is found, None is returned.
    """
    uri = uri.replace('"', '')
    query = 'SELECT ?name WHERE {{ <{0}> rdfs:label ?name }}'.format(uri)
    data = _query(query)
    results = _prepare_results(data)
    if results:
        return results[0].get('name')
    return None

def image_for_name(name, fallback=False, no_uri=False):
    """
    Returns an image URL for a given entity name.
    If none is found, None is returned.

    If `fallback=True`, will fallback to Wikipedia
    for an image.

    If you know there is no URI for the specified name,
    i.e. from having separately called `uri_for_name`,
    you can specify `no_uri=True`, and querying for the
    URI will be skipped. Note that this overrides the user
    value for `fallback` and sets it to `True`.

    Example::

        >>> image_for_name("Star Trek")
        'http://upload.wikimedia.org/wikipedia/commons/7/7e/StarTrek_Logo_2007.JPG'
    """

    uri = None
    image = None
    if not no_uri:
        uri = uri_for_name(name)
        uri = uri.replace('"', '')
        image = image_for_uri(uri) if uri else None
    if (uri is None or image is None) and fallback:
        image = wiki_image_for_name(name)
    return image

def image_for_uri(uri, fallback=False):
    """
    Returns an image URL for a given entity URI.
    If none is found, None is returned.

    If `fallback=True`, will fallback to Wikipedia
    for an image.
    """
    uri = uri.replace('"', '')
    query = 'SELECT ?image_url WHERE {{ <{0}> foaf:depiction ?image_url }}'.format(uri)
    data = _query(query)
    results = _prepare_results(data)
    if results:
        return results[0].get('image_url')
    elif fallback:
        name = name_for_uri(uri)
        return wiki_image_for_name(name)
    return None

def wiki_image_for_name(name):
    """
    Queries Wikipedia for an image for an entity name.
    """
    # Eventually this will get from a locally processed
    # Wikipedia clone database.
    # For now, return None.
    return None

def coordinates_for_name(name):
    """
    Returns a set of coordinates for a given entity name.
    If none is found, None is returned.

    Example::

        >>> coordinates_for_name("Beijing")
        {'lat': '39.90638888888889', 'long': '116.37972222222223'}
    """
    uri = uri_for_name(name)
    uri = uri.replace('"', '')
    return coordinates_for_uri(uri)

def coordinates_for_uri(uri):
    """
    Returns a set of coordinates for a given entity URI.
    If none is found, None is returned.
    """
    uri = uri.replace('"', '')
    query = 'SELECT ?lat ?long WHERE {{ <{0}> geo:lat ?lat; geo:long ?long }}'.format(uri)
    data = _query(query)
    results = _prepare_results(data)
    if results:
        return results[0]
    return None

def summary_for_name(name, short=False, fallback=False, no_uri=False):
    """
    Returns a summary for a given entity name.
    If none is found, None is returned.

    Optionally specify `short=True` to get a
    shorter summary.

    If `fallback=True`, will fallback to Wikipedia
    for a summary.
    Note that this is temporary, and may not necessarily
    return a summary for the correct entity.

    If you know there is no URI for the specified name,
    i.e. from having separately called `uri_for_name`,
    you can specify `no_uri=True`, and querying for the
    URI will be skipped. Note that this overrides the user
    value for `fallback` and sets it to `True`.

    Example::

        >>> summary_for_name("Beijing", short=True)
        "Beijing, sometimes romanized as Peking, is the capital of the People's Republic of China and one of the most populous cities in the world. The population as of 2012 was 20,693,000. The metropolis, located in northern China, is governed as a direct-controlled municipality under the national government, with 14 urban and suburban districts and two rural counties. Beijing Municipality is surrounded by Hebei Province with the exception of neighboring Tianjin Municipality to the southeast."
    """
    # If `no_uri=True`, override user setting for
    # `fallback` and set to True.
    fallback = True if no_uri else fallback

    uri = None
    summary = None
    if not no_uri:
        uri = uri_for_name(name)
        uri = uri.replace('"', '')

        # Override fallback here,
        # so we can just reuse the name from here.
        summary = summary_for_uri(uri, short=short, fallback=False) if uri else None

    if (uri is None or summary is None) and fallback:
        summary = wiki_summary_for_name(name, short=short)
    return summary

def summary_for_uri(uri, short=False, fallback=False):
    """
    Returns a summary for a given entity URI.
    If none is found, None is returned.

    If `fallback=True`, will fallback to Wikipedia
    for a summary.

    Optionally specify `short=True` to get a
    shorter summary.
    """
    uri = uri.replace('"', '')
    predicate = 'rdfs:comment' if short else 'dbo:abstract'
    query = 'SELECT ?summary WHERE {{ <{0}> {1} ?summary }}'.format(uri, predicate)
    data = _query(query)
    results = _prepare_results(data)
    if results:
        return results[0].get('summary')
    elif fallback:
        name = name_for_uri(uri)
        return wiki_summary_for_name(name, short=short)
    return None

def wiki_summary_for_name(name, short=False):
    """
    Queries Wikipedia for a summary for an entity name.
    """
    # Eventually this will get from a locally processed
    # Wikipedia clone database.
    # For now, return None.
    return None

def aliases_for_name(name):
    """
    Returns a list of alias URIs for a given entity name.

    Example::

        >>> aliases_for_name("United States Secretary of State")
        ['http://dbpedia.org/resource/US_Secretary_Of_State',
         'http://dbpedia.org/resource/Secretary_of_State_of_the_United_States',
          'http://dbpedia.org/resource/US_Secretary_of_State', ...]
    """

    uri = uri_for_name(name)
    uri = uri.replace('"', '')
    return aliases_for_uri(uri)

def aliases_for_uri(uri):
    """
    Returns a list of alias URIs for a given entity URI.
    """
    uri = uri.replace('"', '')
    query = 'SELECT ?alias_uri WHERE {{ ?alias_uri dbo:wikiPageRedirects <{0}> }}'.format(uri)
    data = _query(query)
    results = _prepare_results(data)
    return [d['alias_uri'] for d in results]


def knowledge_for(uri=None, name=None, fallback=False):
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
    if uri:
        uri = uri.replace('"', '')
        results['summary'] = summary_for_uri(uri, short=False, fallback=fallback)
        results['image'] = image_for_uri(uri, fallback=fallback)
        results['name'] = name_for_uri(uri)
    elif name:
        results['summary'] = summary_for_name(name, short=False, no_uri=True)
        results['image'] = image_for_name(name, no_uri=True)
        results['name'] = name
    return results


def _query(query):
    data = 'query={0} {1}'.format(PREFIXES, query).encode('utf-8')
    req = request.Request('http://{host}:3030/knowledge/query'.format(host=APP['KNOWLEDGE_HOST']),
            headers={'Accept': 'application/sparql-results+json'},
            data=data)
    res = request.urlopen(req)
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
        ("'", "\\'")
    ]
    for mapping in mappings:
        text = text.replace(mapping[0], mapping[1])
    return text


