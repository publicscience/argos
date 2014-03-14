from tests import RequiresApp
import tests.factories as fac
from datetime import datetime, timedelta

from argos.core.models import Article, Concept

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

    def test_conceptize_creates_new_concepts_if_no_existing_concept_is_found(self):
        self.assertEqual(Concept.query.count(), 0)

        article = fac.article()

        self.assertTrue(Concept.query.count() > 0)
        self.assertEqual(Concept.query.count(), len(article.concepts))

        # There should be a mention for each concept on the article.
        self.assertEqual(len(article.concepts), len(article.mentions))

    def test_conceptize_sets_new_alias_for_existing_concept(self):
        concept = fac.concept()
        uri = concept.uri

        concepts_count = Concept.query.count()

        # The concept should only have one alias to start.
        self.assertEqual(len(concept.aliases), 1)

        # Mock things so we extract one concept with the same URI
        # as the one we just created.
        self.create_patch('argos.core.brain.knowledge.uri_for_name', return_value=uri)
        self.create_patch('argos.core.brain.concepts', return_value=['An concept'])

        # Create the article, which calls conceptize.
        article = Article(title='A title', text='Some text', score=100)

        self.assertEqual(Concept.query.count(), concepts_count)
        self.assertEqual(len(concept.aliases), 2)

        # There should be a mention for each concept on the article.
        self.assertEqual(len(article.concepts), len(article.mentions))

    def test_conceptize_doesnt_set_new_alias_for_existing_concept_with_same_name(self):
        concept = fac.concept()
        uri = concept.uri

        concepts_count = Concept.query.count()
        self.assertEqual(len(concept.aliases), 1)

        # Mock things so we extract one concept with the same URI
        # as the one we just created.
        self.create_patch('argos.core.brain.knowledge.uri_for_name', return_value=uri)
        self.create_patch('argos.core.brain.concepts', return_value=[concept.aliases[0].name])

        # Create the article, which calls conceptize.
        article = Article(title='A title', text='Some text', score=100)

        self.assertEqual(Concept.query.count(), concepts_count)
        self.assertEqual(len(concept.aliases), 1)

        # There should be a mention for each concept on the article.
        self.assertEqual(len(article.concepts), len(article.mentions))

    def test_conceptize_adds_new_mention_for_existing_concept_when_mentioned_name_is_different(self):
        concept = fac.concept()
        uri = concept.uri

        # Mock things so two concepts are returned, but since they share the same uri, they point to the same concept.
        self.create_patch('argos.core.brain.knowledge.uri_for_name', return_value=uri)
        self.create_patch('argos.core.brain.concepts', return_value=['Concept alias one', 'Concept alias two'])

        # Create the article, which calls conceptize.
        article = Article(title='A title', text='Some text', score=100)

        # There should still only be one concept on the article.
        self.assertEqual(len(article.concepts), 1)

        # But there should be two mentions.
        self.assertEqual(len(article.mentions), 2)

        # There should only be one concept.
        self.assertEqual(Concept.query.count(), 1)
        # But three aliases (the original one the
        # concept had, plus the two new ones here).
        self.assertEqual(len(concept.aliases), 3)
