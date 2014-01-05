import unittest
import brain

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

        expected = {
                 'Enrico Fermi Award',
                 'Trinity',
                 'Soviet Union',
                 'Julius Robert Oppenheimer',
                 'Enrico Fermi',
                 'Second Red Scare',
                 'Berkeley',
                 'Phillips',
                 'Born',
                 'American',
                 'University of California',
                 'Bhagavad Gita',
                 'Oppenheimer',
                 'John F. Kennedy',
                 'New Mexico',
                 'World War II',
                 'Institute for Advanced Study in Princeton',
                 'Lyndon B. Johnson',
                 'United States Atomic Energy Commission',
                 'Manhattan Project'
        }

        self.assertEqual(set(results), expected)

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
