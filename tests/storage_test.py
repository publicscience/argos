from tests import RequiresMocks
from unittest.mock import MagicMock

from argos.util import storage

from io import BytesIO

class StorageTest(RequiresMocks):
    def test_save_from_url(self):
        # Mock out S3/Boto.
        key = MagicMock()
        self.create_patch('argos.util.storage.S3Connection', return_value=MagicMock())
        self.create_patch('argos.util.storage.Key', return_value=key)

        # Mock response for downloading.
        image_data = open('tests/data/image.jpg', 'rb').read()
        mock_response = BytesIO(image_data)
        mock_response.headers = {
            'Accept-Ranges': 'bytes',
            'Last-Modified': 'Wed, 05 Sep 2013 08:53:26 GMT',
            'Content-Length': str(len(image_data))
        }
        mock_urlopen = self.create_patch('urllib.request.urlopen', return_value=mock_response)

        storage.save_from_url('http://someurl.com/image.jpg', 'downloaded.jpg')

        # Get the bytes data that the key was given.
        called_data = key.set_contents_from_file.call_args_list[0][0][0].getvalue()
        self.assertEqual(called_data, image_data)
        self.assertEqual(key.key, 'downloaded.jpg')
