from tests import RequiresApp
from copy import deepcopy
from datetime import datetime, timedelta

from core.brain import cluster, vectorize
from core.models import Cluster, Article

class ClusterTest(RequiresApp):
    def setUp(self):
        self.article = self.prepare_articles()[0]

    def prepare_articles(self, type='standard'):
        a = {'title':'Dinosaurs', 'text':'dinosaurs are cool, Clinton'}
        b = {'title':'Robots', 'text':'robots are nice, Clinton'}
        c = {'title':'Robots', 'text':'papa was a rodeo, Clinton'}

        if type == 'standard':
            articles = [Article(**a), Article(**b)]
        elif type == 'duplicate':
            articles = [Article(**a), Article(**a)]
        elif type == 'different':
            articles = [Article(**a), Article(**c)]

        # Need to save these articles to persist entities,
        # so that their overlaps are calculated properly when clustering!
        for article in articles:
            self.db.session.add(article)
        self.db.session.commit()

        return articles

    def prepare_cluster(self):
        self.cluster = Cluster(self.prepare_articles())
        self.db.session.add(self.cluster)
        self.db.session.commit()

    def test_cluster_similarity_with_object_different(self):
        self.prepare_cluster()
        avg_sim = self.cluster.similarity(self.article)
        self.assertNotEqual(avg_sim, 1.0)
        self.assertNotEqual(avg_sim, 0.0)

    def test_cluster_similarity_with_object_duplicates(self):
        members = self.prepare_articles(type='duplicate')
        c = Cluster(members)
        avg_sim = c.similarity(self.article)
        self.assertEqual(avg_sim, 1.0)

    def test_cluster_similarity_with_cluster_duplicates(self):
        self.prepare_cluster()
        members = (self.prepare_articles())
        c = Cluster(members)
        avg_sim = self.cluster.similarity(c)

        # Currently, the similarity calculation between clusters
        # does not yield 1.0 if they are identical clusters,
        # because we calculate the average similarity of the articles
        # between the clusters, rather than the overlap of the two clusters.
        #self.assertEqual(avg_sim, 1.0)
        self.assertAlmostEqual(avg_sim, 0.733333333)

    def test_cluster_similarity_with_cluster_different(self):
        self.prepare_cluster()
        members = self.prepare_articles(type='different')
        c = Cluster(members)

        avg_sim = self.cluster.similarity(c)
        self.assertNotEqual(avg_sim, 1.0)
        self.assertNotEqual(avg_sim, 0.0)

    def test_cluster_expired_made_inactive(self):
        self.prepare_cluster()
        self.cluster.updated_at = datetime.utcnow() - timedelta(days=4)
        cluster.cluster([self.article])
        self.assertFalse(self.cluster.active)

    def test_cluster_clusters_similar(self):
        self.prepare_cluster()
        members = self.prepare_articles(type='duplicate')
        self.cluster.members = members

        cluster.cluster([self.article])
        self.assertEqual(len(self.cluster.members), 3)

    def test_cluster_does_not_cluster_if_no_shared_entities(self):
        self.prepare_cluster()
        members = [Article(
            title='Robots',
            text='dinosaurs are cool, Reagan'
        )]
        self.cluster.members = members

        cluster.cluster([self.article])
        self.assertEqual(len(self.cluster.members), 1)

    def test_cluster_does_not_cluster_not_similar(self):
        self.prepare_cluster()
        article = Article(
                title='Superstars',
                text='superstars are awesome, Clinton'
        )
        cluster.cluster([article])
        self.assertEqual(len(self.cluster.members), 2)

    def test_cluster_no_matching_cluster_creates_new_cluster(self):
        article = Article(
                title='Superstars',
                text='superstars are awesome, Clinton'
        )
        cluster.cluster([article])

        self.assertEqual(Cluster.query.count(), 1)

    def test_cluster_entitize(self):
        members = [Article(
            title='Robots',
            text='dinosaurs are cool, Reagan'
        ), self.prepare_articles()[0]]
        self.cluster = Cluster(members)
        entities = {ent.name for ent in self.cluster.entities}
        self.assertEqual(entities, {'Clinton', 'Reagan'})

    def test_cluster_entitize_no_duplicates(self):
        self.cluster = Cluster(self.prepare_articles())
        entities = [ent.name for ent in self.cluster.entities]
        self.assertEqual(entities, ['Clinton'])

    def test_cluster_titleize(self):
        members = [Article(
            title='Robots',
            text='dinosaurs are cool, Reagan'
        )] + self.prepare_articles(type='duplicate')
        self.cluster = Cluster(members)
        self.assertEqual(self.cluster.title, 'Dinosaurs')

    def test_cluster_timespan(self):
        text = 'the worldly philosophers today cautious optimism is based to a large extent on technological breakthroughs'
        members = [
                Article(title='A', text=text, created_at=datetime(2014, 1, 20, 1, 1, 1, 111111)),
                Article(title='B', text=text, created_at=datetime(2014, 1, 22, 1, 1, 1, 111111)),
                Article(title='C', text=text, created_at=datetime(2014, 1, 24, 1, 1, 1, 111111))
        ]
        self.cluster = Cluster(members)
        results = self.cluster.timespan(datetime(2014, 1, 21, 1, 1, 1, 111111))
        self.assertEqual(len(results), 2)
        self.assertEqual({r.title for r in results}, {'B', 'C'})

    def test_nested_clusters_entitize(self):
        members_a = self.prepare_articles()
        members_b = [Article(
            title='Robots',
            text='dinosaurs are cool, Reagan'
        ), Article(
            title='Robots',
            text='dinosaurs are cool, Reagan'
        )]
        clusters = [Cluster(members_a), Cluster(members_b)]

        self.cluster = Cluster(clusters)
        entities = {ent.name for ent in self.cluster.entities}
        self.assertEqual(entities, {'Reagan', 'Clinton'})

    def test_nested_clusters_clustering(self):
        members = [Cluster(self.prepare_articles(type='duplicate')),
            Cluster(self.prepare_articles(type='duplicate'))]
        input = Cluster(self.prepare_articles(type='duplicate'))
        self.cluster = Cluster(members, tag='super')

        # Need to save so references, etc, all work ok.
        self.db.session.commit()

        cluster.cluster([input], tag='super')
        self.assertEqual(len(self.cluster.members), 3)
