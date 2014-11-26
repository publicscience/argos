"""
Influence Explorer
============

http://data.influenceexplorer.com/api

Federal campaign contribution and lobbying records are from OpenSecrets.org.
State campaign contribution records are from FollowTheMoney.org.
"""

from urllib.parse import urlencode
from urllib import request
import json

from argos.conf import API
KEY = API['SUNLIGHT_API_KEY']

def _request(method, **kwargs):
    url = 'http://transparencydata.com/api/1.0/{method}.json?apikey={key}&{params}'.format(
            method=method,
            key=KEY,
            params=urlencode(kwargs)
          )

    resp = request.urlopen(url).read().decode('utf-8')
    return json.loads(resp)

def recipients_for_organization(profile):
    """
    Gets top recipients for an organization.
    """

    name = profile['name']
    results = []
    raw_orgs = _request('entities', search=name)
    for org_id in [org['id'] for org in raw_orgs]:
        results.append(_request('aggregates/org/{id}/recipients'.format(id=org_id)))

    # For now just using the first result,
    # but it is possible that multiple organizations are returned.
    return {'contributions': results[0]}

def parties_for_organization(profile):
    """
    Gets party contributions for an organization.
    """

    name = profile['name']
    results = []
    raw_orgs = _request('entities', search=name)
    for org_id in [org['id'] for org in raw_orgs]:
        results.append(_request('aggregates/org/{id}/recipients/party_breakdown'.format(id=org_id)))

    # For now just using the first result,
    # but it is possible that multiple organizations are returned.
    return {'party_contributions': results[0]}

def recipients_for_individual(profile):
    """
    Gets top recipients for an individual.
    """

    name = profile['name']
    results = []
    raw_indivs = _request('entities', search=name)
    for indiv_id in [indiv['id'] for indiv in raw_indivs]:
        results.append(_request('aggregates/indiv/{id}/recipient_pols'.format(id=indiv_id)))
    return results

def parties_for_individual(profile):
    """
    Gets party contributions for an individual.
    """

    name = profile['name']
    results = []
    raw_indivs = _request('entities', search=name)
    for indiv_id in [indiv['id'] for indiv in raw_indivs]:
        results.append(_request('aggregates/indiv/{id}/recipients/party_breakdown'.format(id=indiv_id)))
    return results

def organizations_for_individual(profile):
    """
    Gets organization contributions for an individual.
    """

    name = profile['name']
    results = []
    raw_indivs = _request('entities', search=name)
    for indiv_id in [indiv['id'] for indiv in raw_indivs]:
        results.append(_request('aggregates/indiv/{id}/recipient_orgs'.format(id=indiv_id)))
    return results

def contributors_for_politician(profile):
    """
    Gets top contributors for a politician.
    """

    name = profile['name']
    results = []
    raw_pols = _request('entities', search=name)
    for pol_id in [pol['id'] for pol in raw_pols]:
        results.append(_request('aggregates/pol/{id}/contributors'.format(id=pol_id)))
    return results
