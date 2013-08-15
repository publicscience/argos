import unittest
import textutils

class TextUtils(unittest.TestCase):
    def setUp(self):
        pass

    def tearDown(self):
        pass

    def test_trim(self):
        data = '  hey      there           neighbor   '
        self.assertEqual(textutils.trim(data), 'hey there neighbor')

    def test_depunctuate(self):
        data = '[h%e@l&l~o* (t/h>e,r.e:'
        self.assertEqual(textutils.depunctuate(data), ' h e l l o   t h e r e ')

    def test_sanitize(self):
        data = '<html><h1 class="foo">hello there</h1></html>'
        self.assertEqual(textutils.sanitize(data), 'hello there')

if __name__ == '__main__':
	unittest.main()
