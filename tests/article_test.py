from tests import RequiresApp
import tests.factories as fac
from datetime import datetime, timedelta

from argos.core.models import Article

class ArticleTest(RequiresApp):
    def test_article_identical_similarity(self):
        # Identical
        a = fac.article()
        b = fac.article()
        sim = a.similarity(b)
        self.assertEqual(sim, 1.0)

    def test_article_time_bias(self):
        # Identical
        a = fac.article()
        b = fac.article()
        sim = a.similarity(b)

        # Set time difference
        b.created_at = datetime.utcnow() - timedelta(days=10)
        sim_ = a.similarity(b)

        self.assertTrue(sim > sim_)

    def test_article_small_time_bias(self):
        # Identical
        a = fac.article()
        b = fac.article()
        sim = a.similarity(b)

        # Set time difference to be small,
        # small enough that it doesn't affect the score.
        b.created_at = datetime.utcnow() - timedelta(days=1)
        sim_ = a.similarity(b)

        self.assertEqual(sim, sim_)
