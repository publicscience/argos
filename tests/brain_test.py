#!../shallowthought-env/bin/python

import unittest
from brain import Brain

class BrainTest(unittest.TestCase):
    def setUp(self):
        self.b = Brain()

    def tearDown(self):
        self.b = None

    def test_instance(self):
        self.assertIsInstance(self.b, Brain)

    def test_simple_count(self):
        data = "hey there buddy, hey"
        freqs = dict(self.b.count(data))
        self.assertEqual(freqs, {
            'hey': 2,
            'there': 1,
            'buddy': 1
            })

if __name__ == '__main__':
	unittest.main()
