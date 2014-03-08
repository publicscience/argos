from tests import RequiresApp
import tests.factories as fac
from datetime import datetime, timedelta

from argos.core.models import Article, Entity

class ArticleTest(RequiresApp):
    def test_identical_similarity(self):
        # Identical
        a = fac.article()
        b = fac.article()
        sim = a.similarity(b)
        self.assertEqual(sim, 1.0)

    def test_time_bias(self):
        # Identical
        a = fac.article()
        b = fac.article()
        sim = a.similarity(b)

        # Set time difference
        b.created_at = datetime.utcnow() - timedelta(days=10)
        sim_ = a.similarity(b)

        self.assertTrue(sim > sim_)

    def test_small_time_bias(self):
        # Identical
        a = fac.article()
        b = fac.article()
        sim = a.similarity(b)

        # Set time difference to be small,
        # small enough that it doesn't affect the score.
        b.created_at = datetime.utcnow() - timedelta(days=1)
        sim_ = a.similarity(b)

        self.assertEqual(sim, sim_)

    def test_entitize_creates_new_entities_if_no_existing_entity_is_found(self):
        self.assertEqual(Entity.query.count(), 0)

        article = fac.article()

        self.assertTrue(Entity.query.count() > 0)
        self.assertEqual(Entity.query.count(), len(article.entities))

        # There should be a mention for each entity on the article.
        self.assertEqual(len(article.entities), len(article.mentions))

    def test_entitize_sets_new_alias_for_existing_entity(self):
        entity = fac.entity()
        uri = entity.uri

        entities_count = Entity.query.count()

        # The entity should only have one alias to start.
        self.assertEqual(len(entity.aliases), 1)

        # Mock things so we extract one entity with the same URI
        # as the one we just created.
        self.create_patch('argos.core.brain.knowledge.uri_for_name', return_value=uri)
        self.create_patch('argos.core.brain.entities', return_value=['An entity'])

        # Create the article, which calls entitize.
        article = Article(title='A title', text='Some text', score=100)

        self.assertEqual(Entity.query.count(), entities_count)
        self.assertEqual(len(entity.aliases), 2)

        # There should be a mention for each entity on the article.
        self.assertEqual(len(article.entities), len(article.mentions))

    def test_entitize_doesnt_set_new_alias_for_existing_entity_with_same_name(self):
        entity = fac.entity()
        uri = entity.uri

        entities_count = Entity.query.count()
        self.assertEqual(len(entity.aliases), 1)

        # Mock things so we extract one entity with the same URI
        # as the one we just created.
        self.create_patch('argos.core.brain.knowledge.uri_for_name', return_value=uri)
        self.create_patch('argos.core.brain.entities', return_value=[entity.aliases[0].name])

        # Create the article, which calls entitize.
        article = Article(title='A title', text='Some text', score=100)

        self.assertEqual(Entity.query.count(), entities_count)
        self.assertEqual(len(entity.aliases), 1)

        # There should be a mention for each entity on the article.
        self.assertEqual(len(article.entities), len(article.mentions))

    def test_entitize_adds_new_mention_for_existing_entity_when_mentioned_name_is_different(self):
        entity = fac.entity()
        uri = entity.uri

        # Mock things so two entities are returned, but since they share the same uri, they point to the same entity.
        self.create_patch('argos.core.brain.knowledge.uri_for_name', return_value=uri)
        self.create_patch('argos.core.brain.entities', return_value=['Entity alias one', 'Entity alias two'])

        # Create the article, which calls entitize.
        article = Article(title='A title', text='Some text', score=100)

        # There should still only be one entity on the article.
        self.assertEqual(len(article.entities), 1)

        # But there should be two mentions.
        self.assertEqual(len(article.mentions), 2)

        # There should only be one entity.
        self.assertEqual(Entity.query.count(), 1)
        # But three aliases (the original one the
        # entity had, plus the two new ones here).
        self.assertEqual(len(entity.aliases), 3)
