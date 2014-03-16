from tests import RequiresApp
import tests.factories as fac
from tests.helpers import save
from argos.core.models.concept import Concept, Alias, ConceptConceptAssociation

class ConceptTest(RequiresApp):
    def setUp(self):
        self.uri = 'http://fauxpedia.org/resource/argos_argos'

    def test_creates_alias(self):
        # Patch these methods so
        # tests don't require the Fuseki server
        # or a network connection to Wikipedia.
        self._patch_knowledge_for()
        self._patch_uri_for_name(self.uri)

        c = Concept('Argos')
        self.db.session.add(c)
        save()

        self.assertEqual(len(c.aliases), 1)
        self.assertEqual(Alias.query.count(), 1)
        self.assertEqual(Alias.query.first().name, 'Argos')

    def test_sets_slug_from_uri(self):
        self._patch_knowledge_for()
        self._patch_uri_for_name(self.uri)

        c = Concept('Argos')
        self.assertEqual(c.slug, 'argos_argos')

    def test_fallback_slug_if_no_uri(self):
        self._patch_knowledge_for()
        self._patch_uri_for_name(None)

        c = Concept('Argos')
        self.assertEqual(c.slug, 'argos')

    def test_sets_properties_from_knowledge(self):
        self._patch_knowledge_for()
        self._patch_uri_for_name(self.uri)

        c = Concept('Argos')

        self.assertEqual(c.summary, 'this is a fakc.summary for uri {0}'.format(self.uri))
        self.assertEqual(c.image, 'http://www.argos.la/image.jpg')

    def test_sets_properties_from_knowledge_no_uri(self):
        self._patch_knowledge_for()
        self._patch_uri_for_name(None)

        c = Concept('Argos')

        self.assertEqual(c.summary, 'this is a fakc.summary for name Argos'.format(self.uri))
        self.assertEqual(c.image, 'http://www.argos.la/image.jpg')

    def test_related_concepts(self):
        related_concepts = fac.concept(num=2)
        c = Concept('Argos')

        concept_associations = [ConceptConceptAssociation(concept, 1.0) for concept in related_concepts]
        c.concept_associations = concept_associations

        for concept in c.concepts:
            self.assertTrue(c in concept.from_concepts)
            self.assertTrue(concept in c.concepts)

    # Patches
    def _patch_knowledge_for(self):
        mock_func = self.create_patch('argos.core.brain.knowledge.knowledge_for')

        def faux_knowledge_for(name=None, uri=None, fallback=None):
            if uri:
                return {
                    'summary': 'this is a fakc.summary for uri {0}'.format(uri),
                    'image': 'http://www.argos.la/image.jpg',
                    'name': 'Canonical name'
                }
            if name:
                return {
                    'summary': 'this is a fakc.summary for name {0}'.format(name),
                    'image': 'http://www.argos.la/image.jpg',
                    'name': name
                }
            return None

        mock_func.side_effect = faux_knowledge_for

    def _patch_uri_for_name(self, return_value):
        self.create_patch('argos.core.brain.knowledge.uri_for_name', return_value=return_value)
