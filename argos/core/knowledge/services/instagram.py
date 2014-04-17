"""
Instagram
============

http://instagram.com/developer/
"""

from urllib.parse import urlencode
from urllib import request
import json

from argos.conf import APP
CLIENT_ID = APP['INSTAGRAM_CLIENT_ID']

def _request(**kwargs):
    url = 'https://api.instagram.com/v1/media/search?client_id={client_id}&{params}'.format(
            client_id=CLIENT_ID,
            params=urlencode(kwargs)
          )

    resp = request.urlopen(url).read().decode('utf-8')
    return json.loads(resp)['data']

def photos_at_location(lat, lng, distance=2000):
    data = _request(lat=lat, lng=lng, distance=distance)
    return [item['images']['standard_resolution']['url'] for item in data]

