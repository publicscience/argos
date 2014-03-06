from tests import RequiresApp
import tests.factories as fac
from tests.helpers import save
from argos.core.models.entity import Entity, Alias

class EntityTest(RequiresApp):
    def setUp(self):
        self.uri = 'http://fauxpedia.org/resource/argos_argos'

    def test_creates_alias(self):
        # Patch these methods so
        # tests don't require the Fuseki server
        # or a network connection to Wikipedia.
        self._patch_knowledge_for()
        self._patch_uri_for_name(self.uri)

        e = Entity('Argos')
        self.db.session.add(e)
        save()

        self.assertEqual(len(e.aliases), 1)
        self.assertEqual(Alias.query.count(), 1)
        self.assertEqual(Alias.query.first().name, 'Argos')

    def test_sets_slug_from_uri(self):
        self._patch_knowledge_for()
        self._patch_uri_for_name(self.uri)

        e = Entity('Argos')
        self.assertEqual(e.slug, 'argos_argos')

    def test_fallback_slug_if_no_uri(self):
        self._patch_knowledge_for()
        self._patch_uri_for_name(None)

        e = Entity('Argos')
        self.assertEqual(e.slug, 'argos')

    def test_sets_properties_from_knowledge(self):
        self._patch_knowledge_for()
        self._patch_uri_for_name(self.uri)

        e = Entity('Argos')

        self.assertEqual(e.summary, 'this is a fake summary for uri {0}'.format(self.uri))
        self.assertEqual(e.image, 'http://www.argos.la/image.jpg')

    def test_sets_properties_from_knowledge_no_uri(self):
        self._patch_knowledge_for()
        self._patch_uri_for_name(None)

        e = Entity('Argos')

        self.assertEqual(e.summary, 'this is a fake summary for name Argos'.format(self.uri))
        self.assertEqual(e.image, 'http://www.argos.la/image.jpg')


    # Patches
    def _patch_knowledge_for(self):
        mock_func = self.create_patch('argos.core.brain.knowledge.knowledge_for')

        def faux_knowledge_for(name=None, uri=None, fallback=None):
            if uri:
                return {
                    'summary': 'this is a fake summary for uri {0}'.format(uri),
                    'image': 'http://www.argos.la/image.jpg'
                }
            if name:
                return {
                    'summary': 'this is a fake summary for name {0}'.format(name),
                    'image': 'http://www.argos.la/image.jpg'
                }
            return None

        mock_func.side_effect = faux_knowledge_for

    def _patch_uri_for_name(self, return_value):
        self.create_patch('argos.core.brain.knowledge.uri_for_name', return_value=return_value)
