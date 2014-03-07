import unittest
from unittest.mock import patch

import time, socket, subprocess, tempfile

from tests.patches import patch_knowledge, patch_entities

from jobs import workers
from json import loads
from tests import helpers

from argos.web.app import app
from argos.datastore import db

from flask.ext.sqlalchemy import SQLAlchemy

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

    Much of this is ported from the flask-testing library.
    Credit: Dan Jacob & collaborators
    """

    # Mock out calls to Apache Jena/Fuseki.
    patch_knowledge = False

    # Mock out calls to Stanford NER.
    patch_entities = False

    def __call__(self, result=None):
        """
        Sets up the tests without needing
        to call setUp.
        """
        try:
            self._pre_setup()
            self.patchers = []
            if self.patch_knowledge:
                self.patchers.append(patch_knowledge())
            if self.patch_entities:
                self.patchers.append(patch_entities())
            super(RequiresMocks, self).__call__(result)
        finally:
            self._post_teardown()

    def _pre_setup(self):
        self.app = app

        self.client = self.app.test_client()

        self._ctx = self.app.test_request_context()
        self._ctx.push()

        self.db = db

        self.db.create_all()

    def _post_teardown(self):
        for patcher in self.patchers:
            patcher.stop()

        if self._ctx is not None:
            self._ctx.pop()

        del self.app
        del self.client
        del self._ctx

        self.db.session.remove()
        self.db.drop_all()

    def json(self, resp):
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
