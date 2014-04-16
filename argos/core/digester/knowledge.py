"""
Knowledge
==============

Downloads and processes DBpedia dumps.

At time of writing, the available datasets are::

    instance_types
    instance_types_heuristic
    mappingbased_properties
    mappingbased_properties_cleaned
    specific_mappingbased_properties
    labels
    short_abstracts
    long_abstracts
    images
    geo_coordinates
    raw_infobox_properties
    raw_infobox_property_definitions
    homepages
    persondata
    pnd
    interlanguage_links
    article_categories
    category_labels
    skos_categories
    external_links
    wikipedia_links
    page_links
    redirects
    redirects_transitive
    disambiguations
    iri_same_as_uri
    page_ids
    revision_ids
    revision_uris

Refer to http://wiki.dbpedia.org/Downloads for more details.
"""

from argos.util.logger import logger
from argos.util import gullet
from argos.conf import APP

# For collecting dump links.
import re
from html.parser import HTMLParser
from urllib import request

# For processing dump files.
import os
import bz2
import subprocess
import shutil

# Logging.
logger = logger(__name__)

DESIRED_DATASETS = [
    'labels',
    'short_abstracts',
    'long_abstracts',
    'images',
    'redirects',
    'geo_coordinates',
    'persondata',
    'disambiguations',
    'instance_types',
    'mappingbased_properties'
]

DATASETS_PATH = os.path.expanduser(APP['DATASETS_PATH'])

def download(force=False):
    """
    Downloads and extracts the desired DBpedia datasets.

    They are extracted to the app's `DATASETS_PATH` value.
    """

    # Get the desired dataset urls.
    dataset_urls = [dataset_url for dataset_url in get_dataset_urls() if any(setname in dataset_url for setname in DESIRED_DATASETS)]

    for dataset_url in dataset_urls:
        # dc = decompressed
        dc_filepath = os.path.join(DATASETS_PATH,
                os.path.basename(dataset_url)[:-4]) # remove '.bz2'

        if os.path.exists(dc_filepath) and not force:
            logger.warn('File exists, not re-downloading and extracting. You can force by passing `force=True`.')
            continue

        # Download the dataset.
        logger.info('Downloading knowledge dataset from {0}'.format(dataset_url))
        filepath = gullet.download(dataset_url, '/tmp/')
        logger.info('Downloaded to {0}'.format(filepath))

        # Decompress the files.
        logger.info('Extracting to {0}'.format(dc_filepath))
        with open(dc_filepath, 'wb+') as dc_file, bz2.BZ2File(filepath, 'rb') as file:
            for data in iter(lambda : file.read(100 * 1024), b''):
                dc_file.write(data)

        # Clean up.
        os.remove(filepath)
    logger.info('Downloading and extraction complete.')

def digest(force=False):
    """
    Digests downloaded DBpedia `ttl` (Turtle) dumps
    using Apache Jena's `tdbloader2`.

    This digested data can then be interfaced via
    Apache Jena's Fuseki server (see `argos.core.brain.knowledge`).

    Note: `tdbloader2` only runs properly on Unix systems.
    """

    knowledge_path = os.path.join(DATASETS_PATH, 'knodb')
    logger.info('Digesting the datasets to {0}...'.format(knowledge_path))

    if os.path.exists(knowledge_path):
        if not force:
            logger.warn('It looks like a knowledge database already exists, not rebuilding it. You can force by passing `force=True`.')
            return
        logger.warn('Existing knowledge database found. Removing...')
        shutil.rmtree(knowledge_path)

    # Assuming the Argos env is in its default place.
    loader_path = os.path.expanduser('~/env/argos/jena/jena/bin/tdbloader2')
    cmd = [loader_path, '--loc', knowledge_path]
    datasets = [os.path.join(DATASETS_PATH, dataset) for dataset in os.listdir(DATASETS_PATH) if dataset.endswith('.ttl') and any(setname in dataset for setname in DESIRED_DATASETS)]
    logger.info('Using the datasets: {0}'.format(' '.join(datasets)))

    cmd += datasets
    subprocess.call(cmd)
    logger.info('Digestion complete.')

def get_dataset_urls():
    """
    Extracts urls for the different datasets
    from DBpedia.
    """
    url = 'http://wiki.dbpedia.org/Downloads'
    req = request.Request(url)
    resp = request.urlopen(req)
    parser = DumpPageParser()
    parser.feed(resp.read().decode('utf-8', 'ignore'))
    dataset_urls = parser.get_data()
    return dataset_urls

class DumpPageParser(HTMLParser):
    """
    For parsing out pages-articles filenames
    from the Wikipedia latest dump page.
    """
    def __init__(self):
        super().__init__(strict=False)

        # Find the links for the English datasets.
        self.regex = re.compile('\/en\/')
        self.reset()
        self.results = []

    def handle_starttag(self, tag, attrs):
        if tag == 'a':
            for name, value in attrs:
                if name == 'href':
                        if self.regex.findall(value) and value[-7:] == 'ttl.bz2':
                                self.results.append(value)

    def get_data(self):
        return self.results
