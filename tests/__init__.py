import unittest
from unittest.mock import patch
import time, socket, subprocess, tempfile
from cluster.tasks import workers
import time

class RequiresMocks(unittest.TestCase):
    def create_patch(self, name, **kwargs):
        """
        Helper for patching/mocking methods.

        Args:
            | name (str)       -- the 'module.package.method' to mock.
        """
        patcher = patch(name, autospec=True, **kwargs)
        thing = patcher.start()
        self.addCleanup(patcher.stop)
        return thing

class RequiresDB(RequiresMocks):
    @classmethod
    def setUpClass(cls):
        cls.setup_db()

    @classmethod
    def tearDownClass(cls):
        cls.teardown_db()

    @classmethod
    def setup_db(cls):
        # Check if MongoDB is already running.
        s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        try:
            s.connect(('localhost', 27017))
        except (IOError, socket.error):
            # Start MongoDB
            # Note: need to attach the tmpdir to the class,
            # or Python garbage collects it, and the MongoDB closes because
            # its db is gone.
            cls.tmpdir = tempfile.TemporaryDirectory()
            cls.db = cls._run_process(['mongod', '--dbpath', cls.tmpdir.name])

            # Wait until MongoDB is running.
            cls._wait_for_db()

    @classmethod
    def teardown_db(cls):
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

    @classmethod
    def _run_process(cls, cmds):
        """
        Convenience method for running commands.

        Args:
            | cmds (list)   -- list of command args
        """
        return subprocess.Popen(cmds, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)


class RequiresWorkers(RequiresDB):
    @classmethod
    def setupClass(cls):
        cls.setup_db()
        cls.setup_workers()

    @classmethod
    def tearDownClass(cls):
        cls.teardown_db()
        cls.teardown_workers()

    @classmethod
    def setup_workers(cls):
        # Try to run RabbitMQ and a Celery worker.
        # Pipe all output to /dev/null.
        if not workers():
            cls.mq = cls._run_process(['rabbitmq-server'])
            cls.backend = cls._run_process('redis-server')
            cls.worker = cls._run_process(['celery', 'worker', '--config=cluster.celery_config', '--loglevel=INFO', '--logfile=logger/logs/celery.log'])
            # Wait for everything...(need to implement a better checker here)
            time.sleep(5)

    @classmethod
    def teardown_workers(cls):
        # Kill RabbitMQ and Celery.
        if hasattr(cls, 'worker'):
            cls.worker.kill()
        if hasattr(cls, 'mq'):
            cls.mq.kill()
        if hasattr(cls, 'backend'):
            cls.backend.kill()
