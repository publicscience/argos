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
        datetime = '2013-07-07T05:02:36Z'
        num_pagelinks = 735
        title = 'Anarchism'
        redirect = 'Anarchism'

        self.w.digest()

        # Check that page data was added to db.
        # Check that non ns=0 page was ignored.
        self.assertEqual(self.db.count(), 1)

        # Check that page can be fetched by id.
        page = self.db.find({'_id': id})
        self.assertIsNotNone(page)

        # Check proper data.
        self.assertEqual(page['categories'], categories)
        self.assertEqual(len(page['pagelinks']), num_pagelinks)
        self.assertEqual(page['datetime'], datetime)
        self.assertEqual(page['title'], title)
        self.assertEqual(page['redirect'], redirect)

    def test_digest_updates(self):
        id = 12

        self.db.add({
            '_id': id,
            'categories': []
            })
        self.assertEqual(self.db.count(), 1)

        # Check that page can be fetched by id.
        page = self.db.find({'_id': id})
        self.assertIsNotNone(page)

        # Check that categories is empty.
        self.assertEqual(len(page['categories']), 0)

        self.w.digest()
        self.assertEqual(self.db.count(), 1)

        page = self.db.find({'_id': id})
        self.assertIsNotNone(page)

        # Check that categories have been updated.
        self.assertGreater(len(page['categories']), 0)


if __name__ == '__main__':
	unittest.main()
