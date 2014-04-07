import unittest
import time
import socket
import subprocess
from unittest.mock import patch
from json import loads

from argos import web
from argos.web import api, front
from argos.datastore import db
from argos.tasks import workers

from tests.patches import patch_knowledge, patch_concepts, patch_aws
from tests import helpers

test_config = {
        'SQLALCHEMY_DATABASE_URI': 'postgresql://argos_user:password@localhost:5432/argos_test'
}

bare_app = web.create_app(**test_config)
api_app = api.create_app(**test_config)
front_app = front.create_app(**test_config)

for app in [api_app, front_app]:
    app.register_blueprint(helpers.blueprint)


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

class RequiresDatabase(RequiresMocks):
    """
    This class will setup a database
    for the duration of its tests.

    Much of this is ported from the flask-testing library.
    Credit: Dan Jacob & collaborators
    """

    # Mock out calls to Apache Jena/Fuseki.
    patch_knowledge = False

    # Mock out calls to Stanford NER.
    patch_concepts = False

    # Patch interactions with AWS S3.
    patch_aws = True

    def __call__(self, result=None):
        """
        Sets up the tests without needing
        to call setUp.
        """
        try:
            self._setup_app()
            self._pre_setup()
            self.patchers = []
            if self.patch_knowledge:
                self.patchers.append(patch_knowledge())
            if self.patch_concepts:
                self.patchers.append(patch_concepts())
            if self.patch_aws:
                self.patchers.append(patch_aws())
            super(RequiresMocks, self).__call__(result)
        finally:
            self._post_teardown()

    def _setup_app(self):
        self.app = bare_app

    def _pre_setup(self):
        self.client = self.app.test_client()

        self._ctx = self.app.test_request_context()
        self._ctx.push()

        self.db = db

        with self.app.app_context():
            self.db.create_all()

    def _post_teardown(self):
        for patcher in self.patchers:
            patcher.stop()

        if self._ctx is not None:
            self._ctx.pop()

        with self.app.app_context():
            self.db.session.remove()
            self.db.drop_all()

        del self.app
        del self.client
        del self._ctx


    def json(self, resp):
        """
        Load response data into json.
        """
        return loads(resp.data.decode('utf-8'))

class RequiresAPI(RequiresDatabase):
    def  _setup_app(self):
        self.app = api_app

class RequiresFront(RequiresDatabase):
    def  _setup_app(self):
        self.app = front_app
