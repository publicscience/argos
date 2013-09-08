import unittest
from tests import RequiresDB
from unittest.mock import patch, mock_open, MagicMock
from digester import Digester, gullet
from digester.wikidigester import WikiDigester
from tempfile import NamedTemporaryFile
from io import BytesIO
from cluster.tasks import workers
import os, time

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

    def create_patch(self, name):
        """
        Helper for patching/mocking methods.

        Args:
            | name (str)       -- the 'module.package.method' to mock.
        """
        patcher = patch(name, autospec=True)
        thing = patcher.start()
        self.addCleanup(patcher.stop)
        return thing

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
        self.url = 'http://foo.com/%s' % self.file

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


class WikiDigesterTest(unittest.TestCase, RequiresDB):
    @classmethod
    def setUpClass(cls):
        cls.setup_db()

        # Try to run RabbitMQ and a Celery worker.
        # Pipe all output to /dev/null.
        if not workers():
            cls.mq = cls._run_process(['rabbitmq-server'])
            cls.worker = cls._run_process(['celery', 'worker', '--config=cluster.celery_config'])
            # Wait for everything...(need to implement a better checker here)
            time.sleep(5)

    @classmethod
    def tearDownClass(cls):
        cls.teardown_db()

        # Kill RabbitMQ and Celery.
        if cls.worker:
            cls.worker.kill()
        if cls.mq:
            cls.mq.kill()

    def setUp(self):
        # Create the WikiDigester and purge its db.
        self.w = WikiDigester('tests/data/article.xml', db='test')
        self.w.purge()

    def tearDown(self):
        self.w.purge()
        self.w = None

    def test_instance(self):
        self.assertIsInstance(self.w, WikiDigester)

    def test_counts_docs(self):
        self._digest()
        self.assertEqual(self.w.num_docs, 1)

    def test_local_digest(self):
        self._digest()

    def test_distrib_digest(self):
        # Requires that RabbitMQ and a Celery worker are running.
        self.w = WikiDigester('tests/data/article.xml', distrib=True, db='test')
        self.w.purge()
        self._digest()

    def test_distrib_digest_many(self):
        # Requires that RabbitMQ and a Celery worker are running.
        self.w = WikiDigester('tests/data/articles.xml', distrib=True, db='test')
        self.w.purge()
        self._digest_many()

    def test_local_digest_updates(self):
        self._digest_updates()

    def test_distrib_digest_updates(self):
        # Requires that RabbitMQ and a Celery worker are running.
        self.w = WikiDigester('tests/data/article.xml', distrib=True, db='test')
        self.w.purge()
        self._digest_updates()

    def test_tfidf(self):
        # Some fake token ids (hashes).
        docs = [
                [(111, 4), (222, 8), (333, 2)],
                [(111, 8), (333, 4)],
                [(111, 2)],
                [(111, 6), (222, 2)]
        ]

        expected = [
                [[111, 0.0], [222, 8.0], [333, 2.0]],
                [[111, 0.0], [333, 4.0]],
                [[111, 0.0]],
                [[111, 0.0], [222, 2.0]]
        ]

        self.w.num_docs = len(docs)

        docs_tokens = []
        for doc in docs:
            docs_tokens.append([token[0] for token in doc])

        # Add each dummy doc.
        for idx, doc in enumerate(docs):
            self.w.db().add({'title': idx, 'freqs': doc})

        self.w._generate_tfidf(docs_tokens)

        for idx, doc in enumerate(expected):
            tfidf = self.w.db().find({'title': idx })['doc']
            print(tfidf)
            self.assertEquals(dict(doc), dict(tfidf))

    def test_bag_of_words_retrieval(self):
        self.w = WikiDigester('tests/data/simple_article.xml', 'pages', db='test')
        self.w.purge()
        self.w.digest()

        id = 12
        doc = dict([(36962594, 1), (42533182, 1), (70517173, 1), (137495135, 2), (148374140, 2), (190251741, 2), (194249450, 1), (195691240, 1), (252707675, 1), (255853421, 1), (258540396, 2), (288490391, 1), (288949150, 1), (290915221, 2), (307364791, 2), (319357912, 1), (320078809, 2), (321848282, 1), (388039736, 1), (399836250, 1), (470287521, 1), (471008418, 1), (555877666, 1), (637666682, 1)])
        page = self.w.db().find({'_id': id})
        self.assertEqual(dict(page['freqs']), doc)

    def _digest(self):
        id = 12
        categories = [
                'Anarchism',
                'Political culture',
                'Political ideologies',
                'Social theories',
                'Anti-fascism',
                'Anti-capitalism'
                ]
        datetime = '2013-07-07T05:02:36Z'
        num_pagelinks = 735
        title = 'Anarchism'

        self.w.digest()

        if self.w.distrib:
            # There's probably a better way,
            # but if digestion is distrib,
            # wait until the task is complete.
            time.sleep(6)

        # Check that page data was added to db.
        # Check that non ns=0 page was ignored.
        self.assertEqual(self.w.db().count(), 1);

        # Check that page can be fetched by id.
        page = self.w.db().find({'_id': id})
        self.assertIsNotNone(page)

        # Check proper data.
        self.assertEqual(page['categories'], categories)
        self.assertGreaterEqual(len(page['pagelinks']), num_pagelinks)
        self.assertEqual(page['datetime'], datetime)
        self.assertEqual(page['title'], title)

    def _digest_many(self):
        pages = {
                12: 'Anarchism',
                39: 'Albedo',
                308: 'Aristotle',
                309: 'An American in Paris',
                332: 'Animalia (book)',
                334: 'International Atomic Time'
        }

        self.w.digest()

        if self.w.distrib:
            # There's probably a better way,
            # but if digestion is distrib,
            # wait until the task is complete.
            time.sleep(6)

        # Check that page data was added to db.
        # Check that non ns=0 page was ignored.
        self.assertEqual(self.w.db().count(), 6)

        for id, title in pages.items():
            # Check that page can be fetched by id.
            page = self.w.db().find({'_id': id})
            self.assertIsNotNone(page)
            self.assertEqual(page['title'], title)

    def _digest_updates(self):
        id = 12

        self.w.db().add({
            '_id': id,
            'categories': []
            })

        self.assertEqual(self.w.db().count(), 1)

        # Check that page can be fetched by id.
        page = self.w.db().find({'_id': id})
        self.assertIsNotNone(page)

        # Check that categories is empty.
        self.assertEqual(len(page['categories']), 0)

        self.w.digest()

        if self.w.distrib:
            # There's probably a better way,
            # but if digestion is distrib,
            # wait until the task is complete.
            time.sleep(6)

        self.assertEqual(self.w.db().count(), 1)

        page = self.w.db().find({'_id': id})
        self.assertIsNotNone(page)

        # Check that categories have been updated.
        self.assertGreater(len(page['categories']), 0)


if __name__ == '__main__':
    unittest.main()
