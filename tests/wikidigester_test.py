#!../shallowthought-env/bin/python

import unittest
from wikidigester import WikiDigester

class WikiDigesterTest(unittest.TestCase):
    def setUp(self):
        self.w = WikiDigester('tests/data/wiki.xml', 'pages-articles')

    def tearDown(self):
        self.w = None

    def test_instance(self):
        self.assertIsInstance(self.w, WikiDigester)

if __name__ == '__main__':
	unittest.main()
