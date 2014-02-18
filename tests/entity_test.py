from tests import RequiresApp
import tests.factories as fac
from tests.helpers import save

class EntityTest(RequiresApp):

    def test_entity_update_updates_slug(self):
        entity = fac.entity()

        # Sanity check
        self.assertEqual(entity.slug, 'argos')

        entity.name = 'foo bar'
        save()
        self.assertEqual(entity.slug, 'foo-bar')
