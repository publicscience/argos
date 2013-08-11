#!../shallowthought-env/bin/python

import unittest
from wikidigester import WikiDigester
from adipose import Adipose

class WikiDigesterTest(unittest.TestCase):
    def setUp(self):
        self.w = WikiDigester('tests/data/article.xml', 'pages')

        # Setup a test db.
        self.db = Adipose('test', 'pages')
        self.db.empty()
        self.w.db = self.db

    def tearDown(self):
        self.w = None
        self.db.empty()

    def test_instance(self):
        self.assertIsInstance(self.w, WikiDigester)

    def test_digest(self):
        id = 12
        categories = [
                'Anarchism',
                'Political culture',
                'Political ideologies',
                'Social theories',
                'Anti-fascism',
                'Anti-capitalism'
                ]
        num_pagelinks = 735
        self.w.digest()
        self.assertEqual(self.db.count(), 1)

        page = self.db.find({'_id': id})
        self.assertIsNotNone(page)

        self.assertEqual(page['categories'], categories)
        self.assertEqual(len(page['pagelinks']), num_pagelinks)

    def test_digest_updates(self):
        id = 12

        self.db.add({
            '_id': id,
            'categories': []
            })
        self.assertEqual(self.db.count(), 1)

        page = self.db.find({'_id': id})
        self.assertIsNotNone(page)

        self.assertEqual(len(page['categories']), 0)

        self.w.digest()
        self.assertEqual(self.db.count(), 1)

        page = self.db.find({'_id': id})
        self.assertIsNotNone(page)

        self.assertGreater(len(page['categories']), 0)


if __name__ == '__main__':
	unittest.main()
