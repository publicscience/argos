"""
Digest
==============

Digest the full dump, distributed.
The digestion occurs in parts, rather
than processing the entirety the dump as
a single file. Each worker processes a part.
"""

from digester.wikidigester import WikiDigester
from cloud.tasks import celery, workers, notify

# For collecting dump links.
import re
from html.parser import HTMLParser
from urllib import request

# Logging.
import logging
logger = logging.getLogger(__name__)


def main():
    if not workers():
        logger.error('Can\'t start distributed digestion, no workers available or MQ server is not available.')
        return

    # Get a list of all the page dump parts.
    parts = get_parts_urls()

    # Download and digest each part individually.
    for idx, part in enumerate(parts):
        logger.info('Digesting pages dump part %s (%s/%s)' % (part, idx, len(parts)))
        wikidigest.s(url, part)


@celery.task
def wikidigest(url, part):
    w = WikiDigester('/tmp/%s' % part, db='wikidump', url=url+part, silent=False)
    w.digest()

def get_parts_urls():
    """
    Extracts urls for the dump parts
    from Wikimedia's dumps page.
    """
    url = 'http://dumps.wikimedia.org/enwiki/latest/'
    req = request.Request(url)
    resp = request.urlopen(req)
    parser = DumpPageParser()
    parser.feed(resp.read().decode('utf-8'))
    parts = parser.get_data()
    return parts


class DumpPageParser(HTMLParser):
    """
    For parsing out pages-articles filenames
    from the Wikipedia latest dump page.
    """
    def __init__(self):
        super().__init__(strict=False)

        # Find pages-articles chunks filenames.
        self.regex = re.compile('pages-articles\d+')
        self.reset()
        self.results = []

    def handle_data(self, data):
        # Get only bzipped files.
        if self.regex.findall(data) and data[-3:] == 'bz2':
                self.results.append(data)

    def get_data(self):
        return self.results


if __name__ == '__main__':
    main()
