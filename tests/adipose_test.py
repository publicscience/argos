import unittest
import adipose
from adipose import Adipose, InvalidDocument
from operator import itemgetter
from tests import RequiresDB

class AdiposeTest(RequiresDB):
    @classmethod
    def setUpClass(cls):
        cls.setup_db()

    @classmethod
    def tearDownClass(cls):
        cls.teardown_db()

    def setUp(self):
        self.a = Adipose('test', 'test_collection')
        self.a.empty()

    def tearDown(self):
        self.a = None

    def test_instance(self):
        self.assertIsInstance(self.a, Adipose)

    def test_add(self):
        data = {'title': 'foo'}
        self.a.add(data)
        self.assertEqual(self.a.count(), 1)

    def test_empty(self):
        data = {'title': 'foo'}
        self.a.add(data)
        self.a.empty()
        self.assertEqual(self.a.count(), 0)

    def test_add_multiple(self):
        data = [{'title': str(x)} for x in range(20)]
        self.a.add(data)
        self.assertEquals(self.a.count(), 20)

    def test_add_multiple_oversized_doc(self):
        # Save the max message size to restore it.
        true_max_message_size = adipose.MAX_MESSAGE_SIZE
        adipose.MAX_MESSAGE_SIZE = 10
        data = [{'title': 'abcdefghijkl%s' % x} for x in range(10)]
        self.assertRaises(InvalidDocument, self.a.add, data)
        adipose.MAX_MESSAGE_SIZE = true_max_message_size

    def test_add_multiple_oversized_list(self):
        # Save the max message size to restore it.
        true_max_message_size = adipose.MAX_MESSAGE_SIZE
        adipose.MAX_MESSAGE_SIZE = 100
        data = [{'title': 'abcdefghijkl%s' % x} for x in range(20)]
        self.a.add(data)
        self.assertEquals(self.a.count(), 20)
        adipose.MAX_MESSAGE_SIZE = true_max_message_size

    def test_query(self):
        data = {'title': 'foo'}
        self.a.add(data)
        result = self.a.find(data)
        self.assertEquals(result, data)

    def test_all(self):
        data = [
            {'title': 'foo'},
            {'title': 'bar'},
            {'title': 'hey'}
        ]
        for doc in data:
            self.a.add(doc)

        for idx, doc in enumerate(self.a.all()):
            self.assertEquals(data[idx]['title'], doc['title'])

    def test_all_no_limit(self):
        data = [{'title': x} for x in range(1000)]
        for doc in data:
            self.a.add(doc)

        # Sort docs by title so that they go from 0-1000, in order.
        sorted_results = sorted([doc for doc in self.a.all()], key=itemgetter('title'))
        for idx, doc in enumerate(sorted_results):
            self.assertEquals(data[idx]['title'], doc['title'])

    def test_index(self):
        data = [{'title': str(x)} for x in range(20) ]
        self.a.add(data)
        self.a.index('title')

        for x in range(20):
            result = self.a.find({'title': str(x)})
            self.assertEquals(result, data[x])

    def test_update(self):
        data = {'title': 'foo'}
        updated = {'title': 'bar'}

        self.a.add(data)
        self.a.update(data, updated)
        self.assertEquals(self.a.count(), 1)

        result = self.a.find(updated)
        self.assertEquals(result['title'], 'bar')

    def test_save(self):
        data = {'title': 'foo'}
        updated = {'title': 'bar'}

        self.a.add(data)
        doc = self.a.find(data)
        doc['title'] = updated['title']
        self.a.save(doc)

        result = self.a.find(updated)
        self.assertEquals(result['title'], 'bar')


if __name__ == '__main__':
	unittest.main()
