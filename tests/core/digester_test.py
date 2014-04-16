import unittest
from unittest.mock import MagicMock
from tests import RequiresDatabase, RequiresMocks

from argos.core.digester import Digester
import argos.core.digester.knowledge as knowledge

class DigesterTest(unittest.TestCase):
    def setUp(self):
        self.d = Digester('tests/data/article.xml', 'http://www.mediawiki.org/xml/export-0.8')

    def tearDown(self):
        self.d = None

    def test_instance(self):
        self.assertIsInstance(self.d, Digester)

    def test_iterate(self):
        for page in self.d.iterate('page'):
            self.assertIsNotNone(page)

    def test_iterate_bz2(self):
        self.d.file = 'tests/data/article.xml.bz2'
        for page in self.d.iterate('page'):
            self.assertIsNotNone(page)

class KnowledgeTest(RequiresMocks):
    def test_get_dataset_urls(self):
        mock_resp = MagicMock()
        mock_resp.status = 200
        self.create_patch('urllib.request.urlopen', return_value=mock_resp)

        # Load the DBpedia download page html.
        html = open('tests/data/dbpedia_downloads.html', 'rb').read()
        mock_resp.read.return_value = html

        dataset_urls = knowledge.get_dataset_urls()
        self.assertEqual(dataset_urls, ['http://downloads.dbpedia.org/3.9/en/instance_types_en.ttl.bz2', 'http://downloads.dbpedia.org/3.9/en/instance_types_heuristic_en.ttl.bz2', 'http://downloads.dbpedia.org/3.9/en/mappingbased_properties_en.ttl.bz2', 'http://downloads.dbpedia.org/3.9/en/mappingbased_properties_cleaned_en.ttl.bz2', 'http://downloads.dbpedia.org/3.9/en/specific_mappingbased_properties_en.ttl.bz2', 'http://downloads.dbpedia.org/3.9/en/labels_en.ttl.bz2', 'http://downloads.dbpedia.org/3.9/en/short_abstracts_en.ttl.bz2', 'http://downloads.dbpedia.org/3.9/en/long_abstracts_en.ttl.bz2', 'http://downloads.dbpedia.org/3.9/en/images_en.ttl.bz2', 'http://downloads.dbpedia.org/3.9/en/geo_coordinates_en.ttl.bz2', 'http://downloads.dbpedia.org/3.9/en/raw_infobox_properties_en.ttl.bz2', 'http://downloads.dbpedia.org/3.9/en/raw_infobox_property_definitions_en.ttl.bz2', 'http://downloads.dbpedia.org/3.9/en/homepages_en.ttl.bz2', 'http://downloads.dbpedia.org/3.9/en/persondata_en.ttl.bz2', 'http://downloads.dbpedia.org/3.9/en/pnd_en.ttl.bz2', 'http://downloads.dbpedia.org/3.9/en/interlanguage_links_en.ttl.bz2', 'http://downloads.dbpedia.org/3.9/en/article_categories_en.ttl.bz2', 'http://downloads.dbpedia.org/3.9/en/category_labels_en.ttl.bz2', 'http://downloads.dbpedia.org/3.9/en/skos_categories_en.ttl.bz2', 'http://downloads.dbpedia.org/3.9/en/external_links_en.ttl.bz2', 'http://downloads.dbpedia.org/3.9/en/wikipedia_links_en.ttl.bz2', 'http://downloads.dbpedia.org/3.9/en/page_links_en.ttl.bz2', 'http://downloads.dbpedia.org/3.9/en/redirects_en.ttl.bz2', 'http://downloads.dbpedia.org/3.9/en/redirects_transitive_en.ttl.bz2', 'http://downloads.dbpedia.org/3.9/en/disambiguations_en.ttl.bz2', 'http://downloads.dbpedia.org/3.9/en/iri_same_as_uri_en.ttl.bz2', 'http://downloads.dbpedia.org/3.9/en/page_ids_en.ttl.bz2', 'http://downloads.dbpedia.org/3.9/en/revision_ids_en.ttl.bz2', 'http://downloads.dbpedia.org/3.9/en/revision_uris_en.ttl.bz2'])

    def test_digest(self):
        # Limit desired datasets to make things a bit simpler.
        knowledge.DESIRED_DATASETS = [
                'labels',
                'images',
                'redirects'
        ]
        knowledge.DATASETS_PATH = 'tests/data/knowledge/'

        # So we aren't actually deleting anything.
        self.create_patch('shutil.rmtree', return_value=None)

        # So we aren't actually executing any commands.
        mock_call = self.create_patch('subprocess.call', return_value=None)

        knowledge.digest()
        mock_call.assert_called_with(['~/env/argos/jena/jena/bin/tdbloader2', '--loc', 'tests/data/knowledge/knodb', 'tests/data/knowledge/images_en.ttl', 'tests/data/knowledge/labels_en.ttl', 'tests/data/knowledge/redirects_en.ttl'])


if __name__ == '__main__':
    unittest.main()
