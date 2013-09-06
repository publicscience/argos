import unittest
from adipose import Adipose
import socket, subprocess, time
from tempfile import TemporaryDirectory

class AdiposeTest(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        # Check if MongoDB is already running.
        s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        try:
            s.connect(('localhost', 27017))
        except (IOError, socket.error):
            # Start MongoDB
            # Note: need to attach the tmpdir to the class,
            # or Python garbage collects it, and the MongoDB closes because
            # its db is gone.
            cls.tmpdir = TemporaryDirectory()
            cls.db = subprocess.Popen(['mongod', '--dbpath', cls.tmpdir.name], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)

            # Wait until MongoDB is running.
            cls._wait_for_db()

    @classmethod
    def tearDownClass(cls):
        # Kill the db if it's running.
        if hasattr(cls, 'db'):
            cls.db.kill()

    @classmethod
    def _wait_for_db(cls):
        """
        Wait until the database is up and running.
        Thanks to: mongo-python-driver (http://goo.gl/h30mC2)

        Returns:
            | True when database is ready
            | False if database failed to become ready after 160 tries.
        """
        tries = 0
        while cls.db.poll() is None and tries < 160:
            tries += 1
            s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            try:
                try:
                    s.connect(('localhost', 27017))
                    return True
                except (IOError, socket.error) as e:
                    time.sleep(0.25)
            finally:
                s.close()
        return False

    def setUp(self):
        self.a = Adipose('test', 'test_collection')
        self.a.empty()

    def tearDown(self):
        self.a = None

    def test_instance(self):
        self.assertIsInstance(self.a, Adipose)

    def test_add(self):
        data = {'title': 'foo'}
        self.a.add(data)
        self.assertEqual(self.a.count(), 1)

    def test_empty(self):
        data = {'title': 'foo'}
        self.a.add(data)
        self.a.empty()
        self.assertEqual(self.a.count(), 0)

    def test_add_multiple(self):
        data = [{'title': str(x)} for x in range(20) ]
        self.a.add(data)
        self.assertEquals(self.a.count(), 20)

    def test_query(self):
        data = {'title': 'foo'}
        self.a.add(data)
        result = self.a.find(data)
        self.assertEquals(result, data)

    def test_index(self):
        data = [{'title': str(x)} for x in range(20) ]
        self.a.add(data)
        self.a.index('title')

        for x in range(20):
            result = self.a.find({'title': str(x)})
            self.assertEquals(result, data[x])

    def test_update(self):
        data = {'title': 'foo'}
        updated = {'title': 'bar'}

        self.a.add(data)
        self.a.update(data, updated)
        self.assertEquals(self.a.count(), 1)

        result = self.a.find(updated)
        self.assertEquals(result['title'], 'bar')

if __name__ == '__main__':
	unittest.main()
