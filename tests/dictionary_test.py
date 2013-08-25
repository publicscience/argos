import unittest
from digester.dictionary import Dictionary

class DictionaryTest(unittest.TestCase):
    def setUp(self):
        pass

    def tearDown(self):
        pass

    def test_single_doc(self):
        docs = [['space', 'final', 'frontier']]
        d = Dictionary(docs, debug=True)
        expected = {
                7773: 1,
                5435: 1,
                3962: 1
        }
        self.assertEqual(d.freqs, expected)

    def test_multiple_docs(self):
        docs = [
            ['space', 'final', 'frontier'],
            ['final', 'contact', 'galaxy', 'mankind'],
            ['earth', 'space', 'mankind'],
            ['final', 'galaxy', 'frontier']
        ]
        d = Dictionary(docs, debug=True)
        expected = {
                7773: 2,
                5435: 3,
                3962: 2,
                5709: 1,
                1095: 2,
                4979: 2,
                5269: 1
        }
        self.assertEqual(d.freqs, expected)

    def test_hash_equality(self):
        docs = [['space'], ['space'], ['space']]
        d = Dictionary(docs, debug=True)
        expected = { 7773: 3 }
        self.assertEqual(d.freqs, expected)

if __name__ == '__main__':
    unittest.main()
