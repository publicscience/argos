from tests import RequiresDatabase

from argos.core.models import Source

import manage

class ManageTest(RequiresDatabase):
    patch_knowledge = True
    patch_concepts = True

    def test_create_sources(self):
        mock_find_feed = self.create_patch('argos.core.membrane.feed.find_feed')

        url = 'sup'
        mock_find_feed.return_value = url

        manage.create_sources()
        self.assertTrue(Source.query.count() > 1)
