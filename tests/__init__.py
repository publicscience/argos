import unittest
from unittest.mock import patch
import time, socket, subprocess, tempfile
from jobs import workers
from app import app, db
from json import loads


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

class RequiresApp(RequiresMocks):
    """
    This class will setup a database server
    for the duration of its tests.
    """
    def setup_app(self):
        self.app = app.test_client()
        self.app_context = app.test_request_context
        self.db = db
        db.create_all()

    def teardown_app(self):
        db.session.remove()
        db.drop_all()

    def data(self, resp):
        """
        Load response data into json.
        """
        return loads(resp.data.decode('utf-8'))


class RequiresWorkers(RequiresApp):
    """
    This class will setup a RabbitMQ server
    and a Celery worker for the duration of its tests.
    """
    @classmethod
    def setupClass(cls):
        cls.setup_workers()

    @classmethod
    def tearDownClass(cls):
        cls.teardown_workers()

    @classmethod
    def setup_workers(cls):
        # Try to run RabbitMQ and a Celery worker.
        # Pipe all output to /dev/null.
        if not workers():
            cls.mq = cls._run_process(['rabbitmq-server'])
            cls.backend = cls._run_process('redis-server')
            cls.worker = cls._run_process(['celery', 'worker', '--config=conf.CELERY', '--loglevel=INFO', '--logfile=logger/logs/celery.log'])
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

    @classmethod
    def _run_process(cls, cmds):
        """
        Convenience method for running commands.

        Args:
            | cmds (list)   -- list of command args
        """
        return subprocess.Popen(cmds, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
