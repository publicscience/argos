import unittest
from unittest.mock import patch, mock_open, MagicMock
from tempfile import TemporaryFile
from digester import Digester, gullet
from io import BytesIO

class DigesterTest(unittest.TestCase):
    def setUp(self):
        self.d = Digester('tests/data/article.xml', 'http://www.mediawiki.org/xml/export-0.8')

    def tearDown(self):
        self.d = None

    def test_instance(self):
        self.assertIsInstance(self.d, Digester)

    def test_iterate(self):
        for page in self.d.iterate('page'):
            self.assertIsNotNone(page)

    def test_iterate_bz2(self):
        self.d.file = 'tests/data/article.xml.bz2'
        for page in self.d.iterate('page'):
            self.assertIsNotNone(page)


class GulletTest(unittest.TestCase):
    def setUp(self):
        self.data = b"A lot has changed in the past 300 years. People are no longer obsessed with the accumulation of things. We've eliminated hunger, want, the need for possessions. We've grown out of our infancy."

        # Setup file paths and urls.
        self.file = 'test.txt'
        self.url = 'http://foo.com/%s' % self.file
        self.save_path = '/foo/bar'
        self.local_file = '%s/%s' % (self.save_path, self.file)

        # Mock opening and writing the local file.
        self.mock_open = self.create_patch('builtins.open')

        # Mock network communication (opening urls).
        self.mock_urlopen = self.create_patch('urllib.request.urlopen')

        # Mock last modified time for file.
        mock_getmtime = self.create_patch('os.path.getmtime')
        mock_getmtime.return_value = 1378334547.0

        # Mock that the file exists.
        self.create_patch('os.path.exists').return_value = True

        # Mock response from server.
        self.mock_response = MagicMock(
                                headers={
                                    'Accept-Ranges': 'bytes',
                                    'Last-Modified': 'Wed, 05 Sep 2013 08:53:26 GMT',
                                    'Content-Length': '192'
                                }
                             )
        self.mock_urlopen.return_value = self.mock_response

        # Mock iteration (should change this to mock just resp.read())
        self.mock_iter = self.create_patch('builtins.iter')
        self.mock_iter.return_value = [self.data]

    def tearDown(self):
        pass

    def create_patch(self, name):
        """
        Helper for patching/mocking methods.
        """
        patcher = patch(name, autospec=True)
        thing = patcher.start()
        self.addCleanup(patcher.stop)
        return thing

    def create_file(self, complete=False):
        """
        Create a mock file to work with.
        """

        tmpfile = TemporaryFile()

        if complete:
            tmpfile.write(self.data)
        else:
            tmpfile.write(self.data[::2])

        # Mock out the write func.
        tmpfile.write = MagicMock()
        return tmpfile

    def test_detects_expired(self):
        # Set remote file timestamp.
        self.mock_response.headers['Last-Modified'] = 'Wed, 05 Sep 2013 08:53:26 GMT'

        is_expired = gullet._expired('http://www.example.com/foo.bz2', 'foo.bz2')
        self.assertTrue(is_expired)

    def test_detects_not_expired(self):
        # Set remote file timestamp.
        self.mock_response.headers['Last-Modified'] = 'Wed, 01 Sep 2013 08:53:26 GMT'

        is_expired = gullet._expired('http://www.example.com/foo.bz2', 'foo.bz2')
        self.assertFalse(is_expired)

    def test_does_not_download_existing(self):
        # Create the mock response.
        #mock_resp = MagicMock(headers={'Last-Modified':'Wed, 01 Sep 2013 08:53:26 GMT'})
        #self.mock_urlopen.return_value = mock_resp
        pass

    def test_ignores_existing_download(self):
        """
        Download should skip if the file already
        is fully downloaded and is not expired.
        """
        # Set remote file to not be expired.
        self.mock_response.headers['Last-Modified'] = 'Wed, 01 Sep 2013 08:53:26 GMT'

        tmpfile = self.create_file(complete=True)
        self.mock_open.return_value = tmpfile
        gullet.download(self.url, self.save_path)

        tmpfile.write.assert_not_called()
        self.mock_open.assert_called_once_with(self.local_file, 'ab')

    def test_download_continues(self):
        """
        Download should continue if incomplete,
        the file has not expired,
        and the server supports 'Accept-Ranges'.
        """
        # Set remote file to not be expired.
        self.mock_response.headers['Last-Modified'] = 'Wed, 01 Sep 2013 08:53:26 GMT'

        tmpfile = self.create_file()
        self.mock_open.return_value = tmpfile
        gullet.download(self.url, self.save_path)

        tmpfile.write.assert_called()
        self.mock_open.assert_called_once_with(self.local_file, 'ab')

    def test_restarts_expired_download(self):
        """
        Download should restart if the remote
        file is newer than the existing file.
        """

        # Set remote file to be expired.
        self.mock_response.headers['Last-Modified'] = 'Wed, 05 Sep 2013 08:53:26 GMT'

        tmpfile = self.create_file()
        self.mock_open.return_value = tmpfile
        gullet.download(self.url, self.save_path)

        tmpfile.write.assert_called()
        self.mock_open.assert_called_once_with(self.local_file, 'wb')

    def test_restarts_unsupported_download(self):
        """
        Download should restart if the server does not
        support 'Accept-Ranges'.
        """
        # Get rid of the Accept-Ranges header.
        self.mock_response.pop('Accept-Ranges', None)

        tmpfile = self.create_file()
        self.mock_open.return_value = tmpfile
        gullet.download(self.url, self.save_path)

        tmpfile.write.assert_called()
        self.mock_open.assert_called_once_with(self.local_file, 'wb')



if __name__ == '__main__':
    unittest.main()
