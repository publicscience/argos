"""
FeedFinder
==============

Tries to find feeds for
a given URL.

This is essentially a rewrite
of feedfinder.py,
originally by Mark Pilgrim
and Aaron Swartz.

Original is located at:
    http://www.aaronsw.com/2002/feedfinder/

How it works:
    0. At every step, feeds are minimally verified to make sure they are really feeds.
    1. If the URI points to a feed, it is simply returned; otherwise
       the page is downloaded and the real fun begins.
    2. Feeds pointed to by LINK tags in the header of the page (autodiscovery)
    3. <A> links to feeds on the same server ending in ".rss", ".rdf", ".xml", or
       ".atom"
    4. <A> links to feeds on the same server containing "rss", "rdf", "xml", or "atom"
    5. Try some guesses about common places for feeds (index.xml, atom.xml, etc.).
    6. <A> links to feeds on external servers ending in ".rss", ".rdf", ".xml", or
       ".atom"
    7. <A> links to feeds on external servers containing "rss", "rdf", "xml", or "atom"

Copyright:
    2002-2004: Mark Pilgrim
    2006: Aaron Swartz
    2013: Francis Tseng
"""

# Python 2.7 support.
try:
    from urllib import request, parse
except ImportError:
    import urllib2 as request
    import urlparse as parse

import lxml.html
import chardet

def feeds(url):
    """
    Tries to find feeds
    for a given URL.
    """

    url = _full_url(url)
    data = _get(url)

    # Check if the url is a feed.
    if _is_feed(url):
        return [url]

    # Try to get feed links from markup.
    try:
        feed_links = [link for link in _get_feed_links(data, url) if _is_feed(link)]
    except:
        feed_links = []
    if feed_links:
        return feed_links

    # Try 'a' links.
    try:
        links = _get_a_links(data)
    except:
        links = []

    if links:
        # Filter to only local links.
        local_links = [link for link in links if link.startswith(url)]

        # Try to find feed links.
        feed_links.extend(_filter_feed_links(local_links))

        # If still nothing has been found...
        if not feed_links:
            # Try to find feed-looking links.
            feed_links.extend(_filter_feedish_links(local_links))

    # If still nothing has been found...
    if not feed_links:
        # BRUTE FORCE IT!
        guesses = [
                'atom.xml',     # Blogger, TypePad
                'index.atom',   # MoveableType
                'index.rdf',    # MoveableType
                'rss.xml',      # Dave Winer/Manila
                'index.xml',    # MoveableType
                'index.rss',    # Slash
                'feed'          # WordPress
        ]
        tries = [parse.urljoin(url, g) for g in guesses]
        feed_links.extend([link for link in tries if _is_feed(link)])

    # If *still* nothing has been found,
    # just try all the links.
    if links and not feed_links:
            feed_links.extend(_filter_feed_links(links))
            feed_links.extend(_filter_feedish_links(links))

    # Filter out duplicates.
    return list(set(feed_links))


def feed(url):
    feed_links = feeds(url)
    if feed_links:
        return feed_links[0]
    else:
        return None


def _full_url(url):
    """
    Assemble the full url
    for a url.
    """

    url = url.strip()
    for x in ['http', 'https']:
        if url.startswith('%s://' % x):
            return url
    return 'http://%s' % url


def _get_feed_links(data, url):
    """
    Try to get feed links
    defined in the markup.
    """

    FEED_TYPES = ('application/rss+xml',
                  'text/xml',
                  'application/atom+xml',
                  'application/x.atom+xml',
                  'application/x-atom+xml')
    links = []
    html = lxml.html.fromstring(data)

    # For each link...
    for link in html.xpath('//link'):

        # Try to get the 'rel' attribute.
        rel = link.attrib.get('rel', False)
        href = link.attrib.get('href', False)
        type = link.attrib.get('type', False)

        # Check some things.
        if not rel or not href or not type: continue
        if 'alternate' not in rel.split(): continue
        if type not in FEED_TYPES: continue

        links.append(parse.urljoin(url, href))
    return links


def _get_a_links(data):
    """
    Gathers all 'a' links
    from the markup.
    """

    html = lxml.html.fromstring(data)
    return html.xpath('//a/@href')


def _is_feed(url):
    """
    Test if a given URL is
    a feed.
    """

    # If it's not HTTP or HTTPS,
    # it's not a feed.
    scheme = parse.urlparse(url).scheme
    if scheme not in ('http', 'https'):
        return 0

    data = _get(url)

    # If an html tag is present,
    # assume it's not a feed.
    if data.count('<html'):
        return 0

    return data.count('<rss') + data.count('<rdf') + data.count('<feed')


def _is_feed_link(url):
    """
    Check if a link is
    a feed link.
    """
    return url[-4:] in ('.rss', '.rdf', '.xml', '.atom')


def _filter_feed_links(links):
    """
    Filters a list of links
    for only feed links.
    """
    candidates = [link for link in links if _is_feed_link(link)]
    return [link for link in candidates if _is_feed(link)]


def _filter_feedish_links(links):
    """
    Filters a list of links
    for links that *look* like
    they may be feed links.
    """
    feed_links = []
    for link in links:
        if link.count('rss') + link.count('rdf') + link.count('xml') + link.count('atom'):
            if _is_feed(link):
                feed_links.append(link)
    return feed_links


def _get(url):
    """
    Tries to access the url
    and return its data.
    """

    req = request.Request(url)

    try:
        resp = request.urlopen(req)
        body = resp.read()

        # Use Chardet to determine the encoding.
        encoding = chardet.detect(body)['encoding']
        return body.decode(encoding)

    except request.HTTPError as e:
        print('HTTP Error:', e.code, url)
        return ''
    except request.URLError as e:
        print('URL Error:', e.reason, url)
        return ''
    except ConnectionResetError as e:
        print('Connection Error:', e.reason, url)
        return ''
