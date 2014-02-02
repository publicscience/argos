import unittest

import argos.core.brain as brain

class BrainTest(unittest.TestCase):
    def setUp(self):
        pass

    def tearDown(self):
        pass

    def test_tokenize(self):
        data = "hey there buddy, hey Says, say"
        tokens = brain.tokenize(data)
        expected = ['hey', 'buddy', 'hey', 'say', 'say']
        self.assertEqual(tokens,expected)

    def test_entity_recognition(self):
        with open('tests/data/sample.txt', 'r') as f:
            sample = f.read()
        results = brain.entities(sample)

        expected = [
            'Second Red Scare',
            'Bhagavad Gita',
            'Soviet Union',
            'Phillips',
            'John F. Kennedy',
            'Julius Robert Oppenheimer',
            'World War II',
            'Institute for Advanced Study in Princeton',
            'Trinity',
            'Oppenheimer',
            'New Mexico',
            'Lyndon B. Johnson',
            'United States Atomic Energy Commission',
            'University of California',
            'Manhattan Project',
            'Born',
            'Enrico Fermi',
            'American',
            'Berkeley',
            'Enrico Fermi Award',
        ]

        self.assertEqual(set(results), set(expected))

    def test_trim(self):
        data = '  hey      there           neighbor   '
        self.assertEqual(brain.trim(data), 'hey there neighbor')

    def test_depunctuate(self):
        data = '[h%e@l&l~o* (t/h>e,r.e:'
        self.assertEqual(brain.depunctuate(data), ' h e l l o   t h e r e ')

    def test_sanitize(self):
        data = '<html><h1 class="foo">hello there</h1></html>'
        self.assertEqual(brain.sanitize(data), 'hello there')

if __name__ == '__main__':
	unittest.main()
