#!../shallowthought-env/bin/python

import unittest
from digester import Digester

class DigesterTest(unittest.TestCase):
    def setUp(self):
        self.d = Digester('tests/data/article.xml', 'http://www.mediawiki.org/xml/export-0.8')

    def tearDown(self):
        self.d = None

    def test_instance(self):
        self.assertIsInstance(self.d, Digester)

    def test_iterate(self):
        def process_element(elem):
            self.assertIsNotNone(elem)
        self.d.iterate('page', process_element)

if __name__ == '__main__':
    unittest.main()
