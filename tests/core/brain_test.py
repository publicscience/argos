import unittest
from unittest.mock import MagicMock

from tests import RequiresMocks

import argos.core.brain as brain

class BrainTest(RequiresMocks):
    def test_tokenize(self):
        data = "hey there buddy, hey Says, say"
        tokens = brain.vectorizer.tokenize(data)
        expected = ['hey', 'buddy', 'hey', 'say', 'say']
        self.assertEqual(tokens,expected)

    def test_concept_recognition_stanford(self):
        with open('tests/data/sample.txt', 'r') as f:
            sample = f.read()
        results = brain.conceptor.concepts(sample, strategy='stanford')

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
        data = b'''{
          "@text": "Brazilian state-run giant oil company Petrobras signed a three-year technology and research cooperation agreement with oil service provider Halliburton.",
          "@confidence": "0.0",
          "@support": "0",
          "@types": "",
          "@sparql": "",
          "@policy": "whitelist",
          "Resources":   [
                {
              "@URI": "http://dbpedia.org/resource/Brazil",
              "@support": "74040",
              "@types": "Schema:Place,DBpedia:Place,DBpedia:PopulatedPlace,Schema:Country,DBpedia:Country",
              "@surfaceForm": "Brazilian",
              "@offset": "0",
              "@similarityScore": "0.9999203720889515",
              "@percentageOfSecondRank": "7.564391175472872E-5"
            },
                {
              "@URI": "http://dbpedia.org/resource/Petrobras",
              "@support": "387",
              "@types": "DBpedia:Agent,Schema:Organization,DBpedia:Organisation,DBpedia:Company",
              "@surfaceForm": "Petrobras",
              "@offset": "38",
              "@similarityScore": "1.0",
              "@percentageOfSecondRank": "0.0"
            },
                {
              "@URI": "http://dbpedia.org/resource/Halliburton",
              "@support": "458",
              "@types": "DBpedia:Agent,Schema:Organization,DBpedia:Organisation,DBpedia:Company",
              "@surfaceForm": "Halliburton",
              "@offset": "140",
              "@similarityScore": "1.0",
              "@percentageOfSecondRank": "0.0"
            }
          ]
        }'''

        mock_response = MagicMock()
        mock_response.status = 200
        mock_response.read.return_value = data
        self.create_patch('urllib.request.urlopen', return_value=mock_response)

        results = brain.conceptor.concepts('Brazilian state-run giant oil company Petrobras signed a three-year technology and research cooperation agreement with oil service provider Halliburton.', strategy='spotlight')

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
