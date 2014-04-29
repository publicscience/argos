"""
Flickr
============

https://www.flickr.com/services/api/
"""

from urllib.parse import urlencode
from urllib import request
import json

from argos.conf import APP
CLIENT_ID = APP['FLICKR_CLIENT_ID']

def _request(**kwargs):
    url = 'https://api.flickr.com/services/rest/?api_key={api_key}&format=json&nojsoncallback=1&{params}'.format(
            api_key=CLIENT_ID,
            params=urlencode(kwargs)
          )

    resp = request.urlopen(url).read().decode('utf-8')
    return json.loads(resp)

def photos_at_location(lat, lng, distance=20):
    if distance > 32:
        raise Exception('Distance cannot be greater than 32.')

    data = _request(method='flickr.photos.search',
                    sort='interestingness-desc',
                    safe_search=1,      # safe
                    content_type=1,     # no screenshots
                    media='photos',     # no videos
                    license='4,2,1,5',  # CC-BY, CC-NC, CC-NC-SA, CC-SA
                    lat=lat,
                    lon=lng,
                    radius=distance     # radius in km
            )
    photos = data['photos']['photo']
    urls = []
    for photo in photos:
        # Build medium-size urls for each image.
        urls.append('https://farm{farm}.static.flickr.com/{server}/{id}_{secret}_z.jpg'.format(
                farm=photo['farm'],
                server=photo['server'],
                id=photo['id'],
                secret=photo['secret']
             ))
    return urls

