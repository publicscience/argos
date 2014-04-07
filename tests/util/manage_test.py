from tests import RequiresDatabase

from argos.core.models import Source

import manage

from datetime import datetime

class ManageTest(RequiresDatabase):
    patch_knowledge = True
    patch_concepts = True

    def test_create_sources(self):
        mock_find_feed = self.create_patch('argos.core.membrane.feed.find_feed')

        def faux_url(url):
            # so the fake urls remain unique.
            return str(datetime.utcnow())

        mock_find_feed.side_effect = faux_url

        manage.create_sources()
        self.assertTrue(Source.query.count() > 1)
