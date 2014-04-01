from tests import RequiresMocks
from unittest.mock import MagicMock

from argos.util import request

from urllib import error
from io import BytesIO

class RequestTest(RequiresMocks):
    def test_request_retries(self):
        retries = 5
        e = error.HTTPError('some url', 503, 'some msg', '', BytesIO())
        self.mock_open = MagicMock(side_effect=e)

        request.make_request('faux url', max_retries=retries, open_func=self.mock_open)

        self.assertEqual(self.mock_open.call_count, retries)
