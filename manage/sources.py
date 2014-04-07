from argos.core.membrane import feed

import json

from flask.ext.script import Command

from argos.util.logger import logger
logger = logger(__name__)

class CreateSourcesCommand(Command):
    """
    Creates the default set of Sources.
    """
    def run(self):
        create_sources()

def create_sources(filepath='manage/data/sources.json'):
    """
    Load feeds from a JSON file.
    It should consist of an array of arrays like so::

        [
            ["The Atlantic", "http://feeds.feedburner.com/AtlanticNational"],
            ["The New York Times", "http://www.nytimes.com/services/xml/rss/nyt/World.xml"]
        ]
    """
    logger.info('Loading sources from file. This may take awhile...')
    sources = open(filepath, 'r')
    raw_sources = json.load(sources)
    feed.add_sources(raw_sources)
