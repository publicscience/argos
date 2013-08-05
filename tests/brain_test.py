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

if __name__ == '__main__':
	unittest.main()
