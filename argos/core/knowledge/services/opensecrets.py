"""
Open Secrets
============

https://www.opensecrets.org/resources/create/api_doc.php
"""

from urllib.parse import urlencode
from urllib import request
import json

from argos.conf import APP
KEY = APP['OPENSECRETS_API_KEY']

def _request(method, **kwargs):
    url = 'http://api.opensecrets.org/?output=json&method={method}&apikey={key}&{params}'.format(
            method=method,
            key=KEY,
            params=urlencode(kwargs)
          )

    resp = request.urlopen(url).read().decode('utf-8')
    return json.loads(resp)['response']

def organizations(name):
    """
    Gets organizations and information about them.

    Example return value::

        [{
            'name': 'Google Inc',
            'contributions': {
                'democrat': '747341',
                'lobbying': '15800000',
                'republican': '483817',
                'total': '1461482',
                'year': '2014'
            }
        }]
    """

    raw_orgs = _request('getOrgs', org=name)['organization']
    if type(raw_orgs) is list:
        orgs = [org['@attributes']['orgid'] for org in raw_orgs]
    else:
        orgs = [raw_orgs['@attributes']['orgid']]

    results = []
    for orgid in orgs:
        # See https://www.opensecrets.org/api/?method=orgSummary&output=doc
        raw = _request('orgSummary', id=orgid)['organization']['@attributes']
        results.append({
            #'name': raw['orgname'],
            'contributions': {
                'total': raw['total'],
                'lobbying': raw['lobbying'],
                'democrat': raw['dems'],
                'republican': raw['repubs'],
                'year': raw['cycle']
            }
        })

    return results

