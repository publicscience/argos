"""
Feed
==============

Provides an interface for
accessing RSS feeds.

Example::

    # Print articles from a feed.
    site = 'http://www.polygon.com/'
    feed_url = find_feed(site)
    source = Source(feed_url)
    print(articles(source))
"""

from argos.core.membrane import feedfinder
from argos.core.models import Article, Author
from argos.core.brain import entities
from argos.util.gullet import download

import feedparser
import time

from dateutil.parser import parse
from urllib import request, error

from http.client import IncompleteRead
from http.cookiejar import CookieJar
from goose import Goose
from readability.readability import Document

# For feedparser exceptions.
from xml.sax._exceptions import SAXException

g = Goose()

def articles(source):
    """
    Parse a feed from the specified source,
    gathering the latest articles.

    The minimum length of an entry is
    500 characters. Anything under will be ignored.

    This will silently skip articles for which the full text
    can't be retrieved (i.e. if it returns 404).

    Some feeds, for whatever reason, do not include a `published`
    date in their entry data. In which case, it is left as an
    empty string.

    Args:
        | source (Source)    -- the source to fetch from.

    Returns:
        | list -- list of processed latest articles (as dicts).
    """
    # Fetch the feed data.
    data = feedparser.parse(source.ext_url)

    # If the `bozo` value is anything
    # but 0, there was an error parsing (or connecting) to the feed.
    if data.bozo:
        # Some errors are ok.
        if not isinstance(data.bozo_exception, feedparser.CharacterEncodingOverride) and not isinstance(data.bozo_exception, feedparser.NonXMLContentType):
            raise data.bozo_exception

    # Build the entry dicts.
    articles = []
    for entry in data.entries:

        # URL for this entry.
        url = entry['links'][0]['href']

        # Complete HTML content for this entry.
        try:
            entry_data, html = extract_entry_data(url)
            full_text = entry_data.cleaned_text
        except (error.HTTPError, error.URLError) as e:
            if type(e) == error.URLError or e.code == 404:
                continue
            else:
                raise


        # Skip over entries that are too short.
        if len(full_text) < 400:
            continue

        url = entry_data.canonical_link or url
        published = parse(entry.get('published')) or entry_data.publish_date
        updated = parse(entry.get('updated')) or published
        title = entry.get('title', entry_data.title)

        # Download and save the top article image.
        image_url = extract_image(entry_data, filename=hash(url), save_dir='data/images/')

        articles.append(Article(
            ext_url=url,
            source=source,
            html=html,
            text=full_text,
            authors=extract_authors(entry),
            tags=extract_tags(entry, known_tags=entry_data.tags),
            title=title,
            created_at=published,
            updated_at=updated,
            image=image_url
       ))

    return articles

def extract_tags(entry, known_tags=None):
    """
    Extract tags from a feed's entry,
    returning it in a simpler format (a list of strings).

    Args:
        | entry (dict)        -- the entry
        | known_tags (set)    -- known tags

    This operates assuming the tags are formatted like so::

        [{'label': None,
             'scheme': 'http://www.foreignpolicy.com/category/topic/military',
             'term': 'Military'},
        {'label': None,
             'scheme': 'http://www.foreignpolicy.com/category/topic/national_security',
             'term': 'National Security'}]

    This seems to be the standard.

    But there is a fallback if these tags are not supplied.
    Named Entity Recognition is used as a rough approximation of tags.
    (not currently enabled)
    """
    tags = []

    # Use known tags if available.
    if known_tags is not None:
        tags += list(known_tags)

    # If tags are supplied, use them.
    if 'tags' in entry:
        tags += [tag['term'] for tag in entry['tags']]

    return list(set(tags))


    # DISABLING FOR NOW. Easier to run through all entries and add
    # these entities later.
    # Otherwise, try to extract some.
    #else:
        #sample = entry['fulltext']
        #return entities(sample)

def extract_image(entry_data, filename=None, save_dir='.'):
    """
    Extracts and saves a representative
    image for the entry.
    """
    image_url = ''
    if entry_data.top_image:
        remote_image_url = entry_data.top_image.src
        image_url = download(remote_image_url, save_dir, filename=filename)
    return image_url

def extract_authors(entry):
    """
    Extracts authors from an entry,
    creating those that don't exist.

    Args:
        | entry (dict)   -- the entry

    There isn't a consistent way authors are specified
    in feed entries::

        # Seems to be the most common
        "author_detail": {
            "name": "John Heimer"
        }

        # Seems to always come with author_detail, i.e. redundant
        "author": "John Heimer"

        # Have only seen this empty...so ignoring it for now.
        "authors": [
            {}
        ]

        # Sometimes the name is in all caps:
        "author_detail": {
            "name": "JOHN HEIMER"
        }

        # Sometimes authors are combined into a single string,
        # with extra words.
        "author_detail" :{
            "name": "By BEN HUBBARD and HWAIDA SAAD"
        }

    In fact, some feeds use multiple forms!
    """
    names = entry.get('author_detail', {}).get('name') or entry.get('author')

    authors = []

    if names is not None:
        # Parse out the author names.
        names = names.lower()

        # Remove 'by' if its present.
        if names[0:3] == "by ":
            names = names[3:]

        # Split on commas and 'and'.
        names = names.split(',')
        if ' and ' in names[-1]:
            names += names.pop().split(' and ')

        # Remove emptry strings.
        names = list(filter(None, names))

        for name in names:
            name = name.strip().title()
            author = Author.find_or_create(name=name)
            authors.append(author)
    return authors

def find_feed(url):
    """
    Find the RSS feed url for a site.
    Returns the first eligible feed.

    Args:
        | url (str)    -- the url of the site to search.

    Returns:
        | str -- the discovered feed url.
    """
    return feedfinder.feed(url)


def find_feeds(url):
    """
    Find the RSS feed urls for a site.
    Returns all eligible feeds.

    Args:
        | url (str)    -- the url of the site to search.

    Returns:
        | list -- a list of the feed urls.
    """
    return feedfinder.feeds(url)


def extract_entry_data(url):
    """
    Fetch the full content for a feed entry url.

    Args:
        | url (str)    -- the url of the entry.

    Returns:
        | str -- the full text, including html.
    """

    html = _get_html(url)

    # Use Goose to extract data from the raw html,
    # Use readability to give us the html of the main document.
    return g.extract(raw_html=html), Document(html).summary()


def _get_html(url):
    # Some sites, such as NYTimes, track which
    # articles have been viewed with cookies.
    # Without cookies, you get thrown into an infinite loop.
    cookies = CookieJar()
    opener = request.build_opener(request.HTTPCookieProcessor(cookies))

    # Spoof a user agent.
    # This can help get around 403 (forbidden) errors.
    req = request.Request(url, headers={'User-Agent': 'Chrome'})

    # Get the raw html.
    try:
        html = opener.open(req).read()
    except IncompleteRead as e:
        html = e.partial
