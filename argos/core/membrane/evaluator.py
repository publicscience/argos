"""
Evaluator
==============

Collects ranking info about articles,
such as number of shares, likes, tweets, etc.
"""

MAX_RETRIES = 5
from time import sleep

from urllib import request, error, parse
import json

import xmltodict

from argos.util.logger import logger
logger = logger(__name__)

def _request(endpoint, url, format='json'):
    quoted_url = parse.quote(url, safe="%/:=&?~#+!$,;'@()*[]")
    req = request.Request('{0}{1}'.format(endpoint, quoted_url))
    res = request.urlopen(req)
    content = res.read()
    if format == 'json':
        return json.loads(content.decode('utf-8'))
    elif format == 'xml':
        return xmltodict.parse(content)
    return None

def facebook_graph(url):
    """
    Response/Returns::

        {
            'comments': 841,
            'id': 'http://www.google.com',
            'shares': 8503503
        }

    Returns total shares (i.e. likes, shares, and comments) plus the external comments.
    """
    try:
        data = _request('https://graph.facebook.com/', url)
        return data['comments'] + data['shares']
    except error.HTTPError as e:
        logger.exception('Error getting score for `facebook_graph` ({0}): {1}'.format(url, e))
        return 0

def facebook(url):
    """
    Response::

        <links_getStats_response xmlns="http://api.facebook.com/1.0/" xmlns:xsi="http://www.w3.org/2001/XMLSchema-instance" xsi:schemaLocation="http://api.facebook.com/1.0/ http://api.facebook.com/1.0/facebook.xsd" list="true">
            <link_stat>
                <url>www.google.com</url>
                <normalized_url>http://www.google.com/</normalized_url>
                <share_count>5402940</share_count>
                <like_count>1371562</like_count>
                <comment_count>1728901</comment_count>
                <total_count>8503403</total_count>
                <click_count>265614</click_count>
                <comments_fbid>381702034999</comments_fbid>
                <commentsbox_count>841</commentsbox_count>
            </link_stat>
        </links_getStats_response>

    In JSON::

        {
            'click_count': '265614',
            'comment_count': '1728901',
            'comments_fbid': '381702034999',
            'commentsbox_count': '841',
            'like_count': '1371562',
            'normalized_url': 'http://www.google.com/',
            'share_count': '5403040',
            'total_count': '8503503',
            'url': 'www.google.com'
        }

    Returns the click count (weighted by 0.25) plus the share + like + comment counts
    plus the external comments count (`commentsbox_count`).

    Note: `total_count` is the same as `shares` in `facebook_graph`.
    `total_count` is the sum of `comment_count, `like_count`, and `share_count`.

    Note: `commentsbox_count` refers to the number of comments external to Facebook, i.e.
    those that occur on their embedded widgets.

    This differs from `facebook_graph` in that the click count is incorporated (though weighted less).
    """

    try:
        data = _request('https://api.facebook.com/restserver.php?method=links.getStats&urls=', url, format='xml')
        data_ = dict(data['links_getStats_response']['link_stat'])
        return int(data_['click_count'])/4 + int(data_['total_count']) + int(data_['commentsbox_count'])
    except error.HTTPError as e:
        logger.exception('Error getting score for `facebook` ({0}): {1}'.format(url, e))
        return 0


def twitter(url):
    """
    Response/Returns::

        {
            "count":19514340,
            "url":"http:\/\/www.google.com\/"
        }

    Returns the count.

    note::

        This is an undocumented/unofficial endpoint,
        so it could be gone at any moment.
    """
    retries = 0
    while retries < MAX_RETRIES:
        try:
            data = _request('https://cdn.api.twitter.com/1/urls/count.json?url=', url)
            return int(data.get('count', 0))

        except (error.HTTPError) as e:
            if e.code == 503:
                sleep(1*retries)
                retries += 1
            else:
                logger.exception('Error getting score for `twitter` ({0}): {1}'.format(url, e))
                return 0

        # This Twitter endpoint occassionally, for some reason, returns undecodable bytes.
        # This is often resolved after a few tries.
        except UnicodeDecodeError as e:
            sleep(1)
            retries += 1
    return 0


def linkedin(url):
    """
    Response::

        {
            "count":12815,
            "fCnt":"12K",
            "fCntPlusOne":"12K",
            "url":"http:\/\/www.google.com\/"
        }

    Returns the count.
    """
    try:
        data = _request('https://www.linkedin.com/countserv/count/share?format=json&url=', url)
        return int(data['count'])
    except error.HTTPError as e:
        logger.exception('Error getting score for `linkedin` ({0}): {1}'.format(url, e))
        return 0


def stumbleupon(url):
    """
    Response::

        {
            "result": {
                "url":"http:\/\/www.google.com\/",
                "in_index":true,
                "publicid":"2pI1xR",
                "views":254956,
                "title":"Google",
                "thumbnail":"http:\/\/cdn.stumble-upon.com\/mthumb\/31\/10031.jpg",
                "thumbnail_b":"http:\/\/cdn.stumble-upon.com\/bthumb\/31\/10031.jpg",
                "submit_link":"http:\/\/www.stumbleupon.com\/submit\/?url=http:\/\/www.google.com\/",
                "badge_link":"http:\/\/www.stumbleupon.com\/badge\/?url=http:\/\/www.google.com\/",
                "info_link":"http:\/\/www.stumbleupon.com\/url\/www.google.com\/"
            },
            "timestamp":1393894952,
            "success":true
        }

    Returns the view count.
    """
    try:
        data = _request('http://www.stumbleupon.com/services/1.01/badge.getinfo?url=', url)
        return int(data.get('result', {}).get('views', 0))
    except error.HTTPError as e:
        logger.exception('Error getting score for `stumbleupon` ({0}): {1}'.format(url, e))
        return 0


def score(url):
    return round(stumbleupon(url) + linkedin(url) + facebook(url) + twitter(url))
