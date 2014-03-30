"""
Extractor
==============

Extracts data, information and images
for articles.
"""

from argos.core.models import Author
from argos.core.brain import concepts
from argos.util import storage

from http.client import IncompleteRead
from http.cookiejar import CookieJar
from readability.readability import Document
from goose import Goose

from urllib import request, error
from os.path import splitext
from time import sleep

from argos.util.logger import logger
logger = logger(__name__)

g = Goose()

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
    # these concepts later.
    # Otherwise, try to extract some.
    #else:
        #sample = entry['fulltext']
        #return concepts(sample)

def extract_image(entry_data, filename):
    """
    Extracts and saves a representative
    image for the entry.

    This preserves the file extension of the remote file,
    preferencing it over the one specified by the user.
    """
    image_url = None
    if entry_data.top_image:
        remote_image_url = entry_data.top_image.src
        ext = splitext(remote_image_url)[-1].lower()
        image_url = storage.save_from_url(remote_image_url, '{0}{1}'.format(filename, ext))
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


def extract_entry_data(url, max_retries=10):
    """
    Fetch the full content for a feed entry url.

    If a 503 Service Unavailable error is encountered,
    will retry `max_retries` times.

    Args:
        | url (str)    -- the url of the entry.

    Returns:
        | entry_data -- Goose object.
        | str        -- the full text, including html.
    """

    retries = 0
    while True:
        try:
            html = _get_html(url)

            # Use Goose to extract data from the raw html,
            # Use readability to give us the html of the main document.
            return g.extract(raw_html=html), Document(html).summary()

        except (error.HTTPError, ConnectionResetError) as e:
            if (type(e) is ConnectionResetError or e.code == 503) and retries < max_retries:
                # If 503 Service Unavailable,
                # try again after a short delay.
                sleep(1)
                retries += 1
            else:
                raise e




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

    return html
