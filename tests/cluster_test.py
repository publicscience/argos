import unittest
from unittest.mock import MagicMock
from tests import RequiresDB
from datetime import datetime, timedelta
from brain import cluster, vectorize

class ClusterTest(RequiresDB):
    def setUp(self):
        self.faux_cluster = {
            'active': True,
            'title': 'I are cluster',
            'articles': [{
                'text': 'dinosaurs are cool, Clinton',
                'published': datetime.utcnow()
            }, {
                'text': 'robots are nice, Clinton',
                'published': datetime.utcnow()
            }],
            'entities': ['Clinton'],
            'summary': 'This is a summary',
            'created_at': datetime.utcnow(),
            'updated_at': datetime.utcnow()
        }
        self.faux_article = {
                # Expected extracted entity is "Clinton"
                'text': 'dinosaurs are cool, Clinton',
                'published': datetime.utcnow()
        }

        self.mock_database = self.create_patch('brain.cluster.database')
        self.mock_db = MagicMock()
        self.mock_database.return_value = self.mock_db

    def tearDown(self):
        pass

    def test_create_cluster(self):
        c = cluster.Cluster(self.faux_cluster)
        self.assertEqual(c.title, 'I are cluster')
        self.assertEqual(c.summary, 'This is a summary')
        self.assertEqual(c.active, True)

    def test_create_cluster_defaults(self):
        c = cluster.Cluster()
        self.assertEqual(c.active, True)

    def test_cluster_similarity_different(self):
        v = vectorize('dinosaurs are cool')
        c = cluster.Cluster(self.faux_cluster)
        avg_sim = c.similarity(v)
        self.assertNotEqual(avg_sim, 1.0)
        self.assertNotEqual(avg_sim, 0.0)

    def test_cluster_similarity_duplicates(self):
        v = vectorize('dinosaurs are cool, Clinton')
        self.faux_cluster['articles'][1]['text'] = 'dinosaurs are cool, Clinton'
        c = cluster.Cluster(self.faux_cluster)
        avg_sim = c.similarity(v)
        self.assertEqual(avg_sim, 1.0)

    def test_cluster_save(self):
        c = cluster.Cluster(self.faux_cluster)
        c.title = 'foo bar'
        c.save()

        expected = self.faux_cluster
        expected['title'] = 'foo bar'
        self.mock_db.save.assert_called_with(expected)

    def test_cluster_not_expired_kept_active(self):
        c = cluster.Cluster(self.faux_cluster)
        self.mock_clusters = self.create_patch('brain.cluster.clusters', return_value=[c])
        cluster.cluster([self.faux_article])
        self.assertTrue(c.active)

    def test_cluster_expired_made_inactive(self):
        self.faux_cluster['updated_at'] = datetime.utcnow() - timedelta(days=4)
        c = cluster.Cluster(self.faux_cluster)
        self.mock_clusters = self.create_patch('brain.cluster.clusters', return_value=[c])
        cluster.cluster([self.faux_article])
        self.assertFalse(c.active)

    def test_cluster_clusters_similar(self):
        self.faux_cluster['articles'][1]['text'] = 'dinosaurs are cool, Clinton'
        c = cluster.Cluster(self.faux_cluster)
        self.mock_clusters = self.create_patch('brain.cluster.clusters', return_value=[c])
        cluster.cluster([self.faux_article])
        self.assertEqual(len(c.articles), 3)

    def test_cluster_does_not_cluster_if_no_shared_entities(self):
        self.faux_cluster['articles'][1]['text'] = 'dinosaurs are cool, Clinton'
        self.faux_cluster['entities'] = ['Reagan']
        c = cluster.Cluster(self.faux_cluster)
        self.mock_clusters = self.create_patch('brain.cluster.clusters', return_value=[c])
        cluster.cluster([self.faux_article])
        self.assertEqual(len(c.articles), 2)

    def test_cluster_does_not_cluster_not_similar(self):
        self.faux_article['text'] = 'skyscrapers can be enormous, Clinton'
        c = cluster.Cluster(self.faux_cluster)
        self.mock_clusters = self.create_patch('brain.cluster.clusters', return_value=[c])
        cluster.cluster([self.faux_article])
        self.assertEqual(len(c.articles), 2)

    def test_cluster_no_clustering_creates_new_cluster(self):
        self.faux_article['text'] = 'skyscrapers can be enormous, Clinton'
        c = cluster.Cluster(self.faux_cluster)
        self.mock_clusters = self.create_patch('brain.cluster.clusters', return_value=[c])
        cluster.cluster([self.faux_article])

        # If this is called twice, that means a new cluster has been created
        # (since we only started with one)
        self.assertEqual(self.mock_db.save.call_count, 2)

        # Check it was called with the expected article.
        self.assertEqual(self.mock_db.save.call_args_list[-1][0][0]['articles'], [self.faux_article])
