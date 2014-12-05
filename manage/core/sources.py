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

def create_sources(filepath='manage/core/data/sources.json'):
    """
    Load feeds from a JSON file.
    It should consist of an dict of source name => list of feeds like so::

        {
            'The New York Times': [
                'http//www.nytimes.com/services/xml/rss/nyt/World.xml',
                'http//www.nytimes.com/services/xml/rss/nyt/politics.xml'
            ]
        }
    """
    logger.info('Loading sources from file. This may take awhile...')
    sources = open(filepath, 'r')
    raw_sources = json.load(sources)
    feed.add_sources(raw_sources)

