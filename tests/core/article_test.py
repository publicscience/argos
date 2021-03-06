from tests import RequiresDatabase
import tests.factories as fac

from argos.core.models import Article, Concept

class ArticleTest(RequiresDatabase):
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
        self.create_patch('argos.core.knowledge.uri_for_name', return_value=uri)
        self.create_patch('galaxy.concepts', return_value=['An concept'])

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
        self.create_patch('argos.core.knowledge.uri_for_name', return_value=uri)
        self.create_patch('galaxy.concepts', return_value=[concept.aliases[0].name])

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
        self.create_patch('argos.core.knowledge.uri_for_name', return_value=uri)
        self.create_patch('galaxy.concepts', return_value=['Concept alias one', 'Concept alias two'])

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

    def test_conceptize_scores_related_concepts(self):
        # Set things up so two concepts are found
        # when processing the article.
        def mock_uri_for_name(name):
            if name == 'some concept':
                return 'uri_a'
            else:
                return 'uri_b'
        mock_func = self.create_patch('argos.core.knowledge.uri_for_name')
        mock_func.side_effect = mock_uri_for_name

        # One concept appears 3 times, the other only once.
        self.create_patch('galaxy.concepts', return_value=['some concept', 'another concept', 'some concept', 'some concept'])

        # Create the article, which calls conceptize.
        article = Article(title='A title', text='Some text', score=100)

        concepts = article.concepts
        for concept in concepts:
            if concept.uri == 'uri_a':
                self.assertEqual(concept.score, 0.75)
            else:
                self.assertEqual(concept.score, 0.25)
