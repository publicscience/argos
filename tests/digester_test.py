import unittest
from tests import RequiresApp
from digester import Digester
from digester.wikidigester import WikiDigester

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


class WikiDigesterTest(RequiresApp):
    def setUp(self):
        self.setup_app()

        # Create the WikiDigester.
        self.w = WikiDigester('tests/data/article.xml', db='test')

    def tearDown(self):
        self.w = None
        self.teardown_app()

    def test_instance(self):
        self.assertIsInstance(self.w, WikiDigester)

    #def test_counts_docs(self):
        #self._digest()
        #self.assertEqual(self.w.num_docs, 1)

    #def test_digest(self):
        #self._digest()

    #def test_digest_many(self):
        #self.w = WikiDigester('tests/data/articles.xml', db='test')
        #self._digest_many()

    #def test_digest_updates(self):
        #self._digest_updates()

    def test_tfidf(self):
        # Some fake token ids (hashes).
        docs = [
                ( 0, [(111, 4), (222, 8), (333, 2)] ),
                ( 1, [(111, 8), (333, 4)] ),
                ( 2, [(111, 2)] ),
                ( 3, [(111, 6), (222, 2)] )
        ]

        expected = [
                [[111, 0.0], [222, 8.0], [333, 2.0]],
                [[111, 0.0], [333, 4.0]],
                [[111, 0.0]],
                [[111, 0.0], [222, 2.0]]
        ]

        self.w.num_docs = len(docs)

        prepped_docs = []
        for doc in docs:
            tokens = [token[0] for token in doc[1]]
            prepped_docs.append((doc[0], tokens))

        # Add each dummy doc.
        for doc in docs:
            # THIS IS USING THE OLD MONGO/ADIPOSE SYNTAX, need to update it to sqlalchemy
            #self.w.db().add({'_id': doc[0], 'freqs': doc[1]})
            pass

        self.w._generate_tfidf(prepped_docs)

        for idx, doc in enumerate(expected):
            #tfidf = self.w.db().find({'_id': idx })['doc']
            #self.assertEquals(dict(doc), dict(tfidf))
            pass

    #def test_bag_of_words_retrieval(self):
        #self.w = WikiDigester('tests/data/simple_article.xml', db='test')
        #self.w.purge()
        #self.w.digest()

        #id = 12
        #doc = dict([(36962594, 1), (42533182, 1), (70517173, 1), (137495135, 2), (148374140, 2), (190251741, 2), (194249450, 1), (195691240, 1), (252707675, 1), (255853421, 1), (258540396, 2), (288490391, 1), (288949150, 1), (290915221, 2), (307364791, 2), (319357912, 1), (320078809, 2), (321848282, 1), (388039736, 1), (399836250, 1), (470287521, 1), (471008418, 1), (555877666, 1), (637666682, 1)])
        #page = self.w.db().find({'_id': id})
        #self.assertEqual(dict(page['freqs']), doc)

    #def _digest(self):
        #id = 12
        #categories = [
                #'Anarchism',
                #'Political culture',
                #'Political ideologies',
                #'Social theories',
                #'Anti-fascism',
                #'Anti-capitalism'
                #]
        #datetime = '2013-07-07T05:02:36Z'
        #num_pagelinks = 735
        #title = 'Anarchism'

        #self.w.digest()

        ## Check that page data was added to db.
        ## Check that non ns=0 page was ignored.
        #self.assertEqual(self.w.db().count(), 1);

        ## Check that page can be fetched by id.
        #page = self.w.db().find({'_id': id})
        #self.assertIsNotNone(page)

        ## Check proper data.
        #self.assertEqual(page['categories'], categories)
        #self.assertGreaterEqual(len(page['pagelinks']), num_pagelinks)
        #self.assertEqual(page['datetime'], datetime)
        #self.assertEqual(page['title'], title)

    #def _digest_many(self):
        #pages = {
                #12: 'Anarchism',
                #39: 'Albedo',
                #308: 'Aristotle',
                #309: 'An American in Paris',
                #332: 'Animalia (book)',
                #334: 'International Atomic Time'
        #}

        #self.w.digest()

        ## Check that page data was added to db.
        ## Check that non ns=0 page was ignored.
        #self.assertEqual(self.w.db().count(), 6)

        #for id, title in pages.items():
            ## Check that page can be fetched by id.
            #page = self.w.db().find({'_id': id})
            #self.assertIsNotNone(page)
            #self.assertEqual(page['title'], title)

    #def _digest_updates(self):
        #id = 12

        #self.w.db().add({
            #'_id': id,
            #'categories': []
            #})

        #self.assertEqual(self.w.db().count(), 1)

        ## Check that page can be fetched by id.
        #page = self.w.db().find({'_id': id})
        #self.assertIsNotNone(page)

        ## Check that categories is empty.
        #self.assertEqual(len(page['categories']), 0)

        #self.w.digest()

        #self.assertEqual(self.w.db().count(), 1)

        #page = self.w.db().find({'_id': id})
        #self.assertIsNotNone(page)

        ## Check that categories have been updated.
        #self.assertGreater(len(page['categories']), 0)


if __name__ == '__main__':
    unittest.main()
