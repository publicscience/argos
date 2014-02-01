"""
Alchemy
==============

Interface to AlchemyAPI
(for prototyping purposes).
"""

import json
from urllib.request import urlopen
from urllib.parse import urlencode
from conf import ALCHEMY_KEY

API_KEY = ALCHEMY_KEY 
BASE_URL = 'https://access.alchemyapi.com/'

def entities(text):
    params = {'text': text}
    data = request('calls/text/TextGetRankedNamedEntities', params)
    return data['entities']

def concepts(text):
    params = {'text': text}
    data = request('calls/text/TextGetRankedConcepts', params)
    return data['concepts']

def request(endpoint, params):
    url = BASE_URL + endpoint

    params['apikey'] = API_KEY
    params['outputMode'] = 'json'

    params_ = urlencode(params).encode('utf-8')
    resp = urlopen(url, data=params_).read().decode('utf-8')
    return json.loads(resp)
