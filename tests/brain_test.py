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

        expected = [
            ('Phillips', 0.3333333333333333),
            ('Bhagavad Gita', 0.3333333333333333),
            ('Oppenheimer', 1.0),
            ('Institute for Advanced Study in Princeton', 0.3333333333333333),
            ('Second Red Scare', 0.3333333333333333),
            ('Enrico Fermi', 0.3333333333333333),
            ('Berkeley', 0.3333333333333333),
            ('World War II', 0.6666666666666666),
            ('American', 0.6666666666666666),
            ('Soviet Union', 0.3333333333333333),
            ('Manhattan Project', 0.3333333333333333),
            ('Lyndon B. Johnson', 0.3333333333333333),
            ('John F. Kennedy', 0.3333333333333333),
            ('Born', 0.3333333333333333),
            ('Julius Robert Oppenheimer', 0.3333333333333333),
            ('Trinity', 0.3333333333333333),
            ('New Mexico', 0.3333333333333333),
            ('University of California', 0.3333333333333333),
            ('Enrico Fermi Award', 0.3333333333333333),
            ('United States Atomic Energy Commission', 0.3333333333333333)
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
