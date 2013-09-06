import unittest
from adipose import Adipose
from tests import RequiresDB

class AdiposeTest(unittest.TestCase, RequiresDB):
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
        data = [{'title': str(x)} for x in range(20) ]
        self.a.add(data)
        self.assertEquals(self.a.count(), 20)

    def test_query(self):
        data = {'title': 'foo'}
        self.a.add(data)
        result = self.a.find(data)
        self.assertEquals(result, data)

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

if __name__ == '__main__':
	unittest.main()
