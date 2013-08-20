import unittest
import brain

class BrainTest(unittest.TestCase):
    def setUp(self):
        pass

    def tearDown(self):
        pass

    def test_simple_count(self):
        data = "hey there buddy, hey"
        freqs = brain.count(data)

        # 'there' is filtered out as a stopword.
        expected = {
                'hey': 2,
                'buddy': 1
        }
        self.assertEqual(freqs, expected)

    def test_entity_recognition(self):
        with open('tests/data/sample.txt', 'r') as f:
            sample = f.read()
        results = brain.recognize(sample)

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
