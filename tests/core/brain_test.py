import unittest
from unittest.mock import MagicMock

from tests import RequiresMocks

import argos.core.brain as brain

class BrainTest(unittest.TestCase):
    def test_tokenize(self):
        data = "hey there buddy, hey Says, say"
        tokens = brain.tokenize(data)
        expected = ['hey', 'buddy', 'hey', 'say', 'say']
        self.assertEqual(tokens,expected)

    def test_concept_recognition_stanford(self):
        with open('tests/data/sample.txt', 'r') as f:
            sample = f.read()
        results = brain.concepts(sample, strategy='stanford')

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

    def test_concept_recognition_spotlight(self):
        results = brain.concepts('Brazilian state-run giant oil company Petrobras signed a three-year technology and research cooperation agreement with oil service provider Halliburton.', strategy='spotlight')

        expected = [
            'Brazilian',
            'Petrobras',
            'Halliburton'
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
