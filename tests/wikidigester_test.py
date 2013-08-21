import unittest
from digester.wikidigester import WikiDigester
from adipose import Adipose

from time import sleep

class WikiDigesterTest(unittest.TestCase):
    def setUp(self):
        self.w = WikiDigester('tests/data/article.xml', 'pages', db='test')
        self.w.purge()

    def tearDown(self):
        self.w.purge()
        self.w = None

    def test_instance(self):
        self.assertIsInstance(self.w, WikiDigester)

    def test_local_digest(self):
        self._digest()

    def test_distrib_digest(self):
        # Requires that RabbitMQ and a Celery worker are running.
        self.w = WikiDigester('tests/data/article.xml', 'pages', distrib=True, db='test')
        self.w.purge()
        self._digest()

    def test_local_digest_updates(self):
        self._digest_updates()

    def test_distrib_digest_updates(self):
        # Requires that RabbitMQ and a Celery worker are running.
        self.w = WikiDigester('tests/data/article.xml', 'pages', distrib=True, db='test')
        self.w.purge()
        self._digest_updates()

    def _digest(self):
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

        self.w.digest()

        if self.w.distrib:
            # There's probably a better way,
            # but if digestion is distrib,
            # wait until the task is complete.
            sleep(6)

        # Check that page data was added to db.
        # Check that non ns=0 page was ignored.
        self.assertEqual(self.w.db().count(), 1)

        # Check that page can be fetched by id.
        page = self.w.db().find({'_id': id})
        self.assertIsNotNone(page)

        # Check proper data.
        self.assertEqual(page['categories'], categories)
        self.assertGreaterEqual(len(page['pagelinks']), num_pagelinks)
        self.assertEqual(page['datetime'], datetime)
        self.assertEqual(page['title'], title)

    def _digest_updates(self):
        id = 12

        self.w.db().add({
            '_id': id,
            'categories': []
            })

        self.assertEqual(self.w.db().count(), 1)

        # Check that page can be fetched by id.
        page = self.w.db().find({'_id': id})
        self.assertIsNotNone(page)

        # Check that categories is empty.
        self.assertEqual(len(page['categories']), 0)

        self.w.digest()

        if self.w.distrib:
            # There's probably a better way,
            # but if digestion is distrib,
            # wait until the task is complete.
            sleep(6)

        self.assertEqual(self.w.db().count(), 1)

        page = self.w.db().find({'_id': id})
        self.assertIsNotNone(page)

        # Check that categories have been updated.
        self.assertGreater(len(page['categories']), 0)


if __name__ == '__main__':
	unittest.main()
