from tests import RequiresApp
from copy import deepcopy
from datetime import datetime, timedelta
from brain import cluster, vectorize
from models import Cluster, Article

class ClusterTest(RequiresApp):
    def setUp(self):
        self.setup_app()
        self.members = [
                Article(
                    title='Dinosaurs',
                    text='dinosaurs are cool, Clinton'
                ),
                Article(
                    title='Robots',
                    text='robots are nice, Clinton'
                )
        ]
        # Using a copy of the members so identical clusters
        # can be made without messing up references.
        self.cluster = Cluster(deepcopy(self.members))
        self.article = Article(
            title='Dinosaurs',
            text='dinosaurs are cool, Clinton'
        )

        self.db.session.add(self.cluster)
        self.db.session.commit()

    def tearDown(self):
        self.teardown_app()

    def test_cluster_similarity_with_object_different(self):
        avg_sim = self.cluster.similarity_with_object(self.article)
        self.assertNotEqual(avg_sim, 1.0)
        self.assertNotEqual(avg_sim, 0.0)

    def test_cluster_similarity_with_object_duplicates(self):
        members = [self.members[0], self.members[0]]
        c = Cluster(members)
        avg_sim = c.similarity_with_object(self.article)
        self.assertEqual(avg_sim, 1.0)

    def test_cluster_similarity_with_cluster_duplicates(self):
        c = Cluster(deepcopy(self.members))
        avg_sim = self.cluster.similarity_with_cluster(c)
        self.assertEqual(avg_sim, 1.0)

    def test_cluster_similarity_with_cluster_different(self):
        members = [deepcopy(self.members[0]), Article(title='Robots',text='papa was a rodeo, Clinton')]
        c = Cluster(members)

        avg_sim = self.cluster.similarity_with_cluster(c)
        self.assertNotEqual(avg_sim, 1.0)
        self.assertNotEqual(avg_sim, 0.0)

    def test_cluster_expired_made_inactive(self):
        self.cluster.updated_at = datetime.utcnow() - timedelta(days=4)
        cluster.cluster([self.article])
        self.assertFalse(self.cluster.active)

    def test_cluster_clusters_similar(self):
        # Create a cluster of identical articles,
        # to ensure greatest similarity.
        members = [self.members[0], deepcopy(self.members[0])]
        self.cluster.members = members

        cluster.cluster([self.article])
        self.assertEqual(len(self.cluster.members), 3)

    def test_cluster_does_not_cluster_if_no_shared_entities(self):
        members = [Article(
            title='Robots',
            text='dinosaurs are cool, Reagan'
        )]
        self.cluster.members = members

        cluster.cluster([self.article])
        self.assertEqual(len(self.cluster.members), 1)

    def test_cluster_does_not_cluster_not_similar(self):
        article = Article(
                title='Superstars',
                text='superstars are awesome, Clinton'
        )
        cluster.cluster([article])
        self.assertEqual(len(self.cluster.members), 2)

    def test_cluster_no_clustering_creates_new_cluster(self):
        article = Article(
                title='Superstars',
                text='superstars are awesome, Clinton'
        )
        cluster.cluster([article])

        # Check for 2 since we only started with one.
        self.assertEqual(Cluster.query.count(), 2)
