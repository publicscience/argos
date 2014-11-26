"""
Instagram
============

http://instagram.com/developer/
"""

from urllib.parse import urlencode
from urllib import request
import json

from argos.conf import API
CLIENT_ID = API['INSTAGRAM_CLIENT_ID']

def _request(**kwargs):
    url = 'https://api.instagram.com/v1/media/search?client_id={client_id}&{params}'.format(
            client_id=CLIENT_ID,
            params=urlencode(kwargs)
          )

    resp = request.urlopen(url).read().decode('utf-8')
    return json.loads(resp)['data']

def photos_at_location(profile):
    lat, lng = profile['latitude'], profile['longitude']

    distance = 2000
    if 'http://dbpedia.org/ontology/Country' in profile['types']:
        distance = 3200
    elif 'http://dbpedia.org/ontology/Region' in profile['types']:
        distance = 2600
    # etc

    data = _request(lat=lat, lng=lng, distance=distance)
    return {'photos': [item['images']['standard_resolution']['url'] for item in data]}

