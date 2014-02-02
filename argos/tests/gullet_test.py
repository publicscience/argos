import os
import unittest

from tests import RequiresMocks
from unittest.mock import mock_open

from core.digester import gullet

from tempfile import NamedTemporaryFile
from io import BytesIO

class GulletTest(RequiresMocks):
    def setUp(self):
        self.data = b"A lot has changed in the past 300 years. People are no longer obsessed with the accumulation of things. We've eliminated hunger, want, the need for possessions. We've grown out of our infancy."


        # Mock opening and writing the local file.
        self.mock_open = self.create_patch('builtins.open')

        # Mock last modified time for file.
        mock_getmtime = self.create_patch('os.path.getmtime')
        mock_getmtime.return_value = 1378334547.0

        # Mock that the file exists.
        self.create_patch('os.path.exists').return_value = True

        # Mock network communication (opening urls) and
        # and mock response from server.
        self.mock_urlopen = self.create_patch('urllib.request.urlopen')
        self.content_length = len(self.data)

    def tearDown(self):
        pass

    def mock_file(self, complete=False):
        """
        Create a named mock existing download file to work with.

        Args:
            | complete (bool)  -- True = the file is a completed download,
                                  False = the file is only partially completed.
        """
        tmpfile = NamedTemporaryFile()

        if complete:
            tmpfile.write(self.data)
        else:
            # Start with the first 12 bytes.
            tmpfile.write(self.data[:12])

        # Setup file paths and urls.
        self.save_path, self.file = os.path.split(tmpfile.name)
        self.url = 'http://foo.com/{0}'.format(self.file)

        return tmpfile

    def mock_response(self, partial=False):
        """
        Create a mock HTTP response to work with.

        Args:
            | partial (bool)  -- True = only the 'remaining' bytes are sent,
                                 False = all the bytes are sent.
        """
        if partial:
            # Start after the first 12 bytes.
            mock_response = BytesIO(self.data[12:])
        else:
            mock_response = BytesIO(self.data)
        mock_response.headers = {
            'Accept-Ranges': 'bytes',
            'Last-Modified': 'Wed, 05 Sep 2013 08:53:26 GMT',
            'Content-Length': str(self.content_length)
        }
        self.mock_urlopen.return_value = mock_response
        return mock_response

    def test_detects_expired(self):
        # Set remote file timestamp.
        mock_resp = self.mock_response()
        mock_resp.headers['Last-Modified'] = 'Wed, 05 Sep 2013 08:53:26 GMT'

        is_expired = gullet._expired('http://www.example.com/foo.bz2', 'foo.bz2')
        self.assertTrue(is_expired)

    def test_detects_not_expired(self):
        # Set remote file timestamp.
        mock_resp = self.mock_response()
        mock_resp.headers['Last-Modified'] = 'Wed, 01 Sep 2013 08:53:26 GMT'

        is_expired = gullet._expired('http://www.example.com/foo.bz2', 'foo.bz2')
        self.assertFalse(is_expired)

    def test_ignores_existing_download(self):
        """
        Download should skip if the file already
        is fully downloaded and is not expired.
        """
        # Set remote file to not be expired.
        mock_resp = self.mock_response()
        mock_resp.headers['Last-Modified'] = 'Wed, 01 Sep 2013 08:53:26 GMT'

        tmpfile = self.mock_file(complete=True)
        self.mock_open.return_value = tmpfile
        gullet.download(self.url, self.save_path)

        # Should have opened new file to append to,
        # but not actually write anything.
        self.assertEquals(tmpfile.tell(), self.content_length)
        self.mock_open.assert_called_once_with(tmpfile.name, 'ab')

    def test_download_continues(self):
        """
        Download should continue if incomplete,
        the file has not expired,
        and the server supports 'Accept-Ranges'.
        """
        # Set remote file to not be expired.
        mock_resp = self.mock_response(partial=True)
        mock_resp.headers['Last-Modified'] = 'Wed, 01 Sep 2013 08:53:26 GMT'

        tmpfile = self.mock_file()
        self.mock_open.return_value = tmpfile
        gullet.download(self.url, self.save_path)

        # Should have appended to existing file.
        self.assertEquals(tmpfile.tell(), self.content_length)
        self.mock_open.assert_called_once_with(tmpfile.name, 'ab')

    def test_restarts_expired_download(self):
        """
        Download should restart if the remote
        file is newer than the existing file.
        """

        # Set remote file to be expired.
        mock_resp = self.mock_response()
        mock_resp.headers['Last-Modified'] = 'Wed, 05 Sep 2013 08:53:26 GMT'

        tmpfile = self.mock_file()
        self.mock_open.return_value = tmpfile
        gullet.download(self.url, self.save_path)

        # Should have written to new file.
        self.assertEquals(tmpfile.tell(), self.content_length)
        self.mock_open.assert_called_once_with(tmpfile.name, 'wb')

    def test_restarts_unsupported_download(self):
        """
        Download should restart if the server does not
        support 'Accept-Ranges'.
        """
        # Set remote file to not be expired, and
        # Get rid of the Accept-Ranges header.
        mock_resp = self.mock_response()
        mock_resp.headers['Last-Modified'] = 'Wed, 01 Sep 2013 08:53:26 GMT'
        mock_resp.headers.pop('Accept-Ranges', None)

        tmpfile = self.mock_file()
        self.mock_open.return_value = tmpfile
        gullet.download(self.url, self.save_path)

        # Should have written to new file.
        self.assertEquals(tmpfile.tell(), self.content_length)
        self.mock_open.assert_called_with(tmpfile.name, 'wb')

