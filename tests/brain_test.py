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

        # 'there' is filtered out as a stopword.
        expected = {
                'hey': 2,
                'buddy': 1
        }
        self.assertEqual(freqs, expected)

    def test_entity_recognition(self):
        with open('tests/data/sample.txt', 'r') as f:
            sample = f.read()
        results = self.b.recognize(sample)

        expected = {
                'Trinity',
                'Julius Robert Oppenheimer',
                'California',
                'New Mexico',
                'American',
                'Berkeley',
                'Advanced Study',
                'Enrico Fermi',
                'Soviet Union',
                'Princeton',
                'Johnson',
                'Oppenheimer',
                'Bhagavad Gita',
                'United States Atomic Energy Commission',
                'Lyndon',
                'Manhattan Project',
                'Enrico Fermi Award',
                'Second Red Scare',
                'University',
                'John'
        }

        self.assertEqual(results, expected)

if __name__ == '__main__':
	unittest.main()
