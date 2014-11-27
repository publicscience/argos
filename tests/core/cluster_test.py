from tests import RequiresDatabase
from datetime import datetime, timedelta

from argos.core.brain import cluster
from argos.core.models import Article, Event

class ClusterTest(RequiresDatabase):
    patch_knowledge = True
    patch_concepts = True

    def setUp(self):
        cluster.PATH = '/tmp/argos_test_hierarchy'
        cluster.h = cluster.Hierarchy(metric='euclidean',
                                      lower_limit_scale=0.9,
                                      upper_limit_scale=1.1)

    def prepare_articles(self, type='standard'):
        a = {'title':'Dinosaurs', 'text':'dinosaurs are cool, Clinton', 'score':100}
        b = {'title':'Robots', 'text':'robots are nice, Clinton', 'score':100}
        c = {'title':'Robots', 'text':'papa was a rodeo, Reagan', 'score':100}

        if type == 'standard':
            articles = [Article(**a), Article(**b)]
        elif type == 'duplicate':
            articles = [Article(**a), Article(**a)]
        elif type == 'different':
            articles = [Article(**a), Article(**c)]

        # Need to save these articles to persist concepts,
        # so that their overlaps are calculated properly when clustering!
        for article in articles:
            self.db.session.add(article)
        self.db.session.commit()

        return articles

    def test_triage(self):
        existing = {
            1: [0,1,2,3],
            2: [4,5],
            3: [6],
            4: [7,8,9],
            5: [10,11,12,13]
        }
        new = [[0,1,2], [3,4,5], [6], [7], [8,9,10]]

        to_update, to_create, to_delete, unchanged = cluster.triage(existing, new)

        # to_update => {event_id: [article_id, ...], ...}
        self.assertEqual(to_update, {1: [0,1,2], 2: [3,4,5], 4: [8,9,10]})

        # to_create => [[article_id, ...], ...]
        self.assertEqual(to_create, [[7]])

        # unchanged => [event_id, ...]
        self.assertEqual(to_delete, [5])

        # unchanged => [event_id, ...]
        self.assertEqual(unchanged, [3])

    def test_cluster_creates_events(self):
        self.assertEqual(Event.query.count(), 0)

        # Since there are no events yet, we expect at least one to be created.
        articles = self.prepare_articles()
        cluster.cluster(articles, min_articles=1)

        self.assertTrue(Event.query.count() > 0)

    def test_cluster_freezes_events(self):
        articles = self.prepare_articles(type='different')
        cluster.cluster(articles, min_articles=1)

        self.assertEqual(Event.query.count(), 2)

        for event in Event.query.all():
            self.assertTrue(event.active)
            if articles[1] in event.members:
                # Fake things and set the event we expect not to have new articles to be old.
                event.updated_at = event.updated_at - timedelta(days=4)

        # These two articles should be identical to the first one.
        new_articles = self.prepare_articles(type='duplicate')
        cluster.cluster(new_articles)

        # One event gets updated, one doesn't.
        for event in Event.query.all():
            if articles[1] in event.members:
                self.assertFalse(event.active)
            else:
                self.assertTrue(event.active)

    def test_cluster_updates_events(self):
        articles = self.prepare_articles(type='different')
        cluster.cluster(articles, min_articles=1)

        self.assertEqual(Event.query.count(), 2)
        for event in Event.query.all():
            self.assertEqual(event.members.count(), 1)

        # These two articles should be identical to the first one.
        new_articles = self.prepare_articles(type='duplicate')
        cluster.cluster(new_articles, min_articles=1)

        # The number of events should not have changed.
        self.assertEqual(Event.query.count(), 2)

        # One event should have 3 articles.
        for event in Event.query.all():
            if articles[1] in event.members:
                self.assertEqual(event.members.count(), 1)
            else:
                self.assertEqual(event.members.count(), 3)

    def test_cluster_minimum_articles(self):
        # Create articles and slice such that we expect one cluster of 2 articles and one of 1 article.
        articles = self.prepare_articles(type='different') + self.prepare_articles(type='different')
        articles = articles[:3]

        # Require a minimum of two articles to create an event.
        cluster.cluster(articles, min_articles=2)

        # So we should only have one event.
        self.assertEqual(Event.query.count(), 1)
        self.assertEqual(Event.query.first().members.all(), [articles[0], articles[2]])

    def test_cluster_minimum_articles_deletes(self):
        articles = self.prepare_articles(type='different') + self.prepare_articles(type='different')
        cluster.cluster(articles, min_articles=2)

        # We should have two events first.
        self.assertEqual(Event.query.count(), 2)

        # Get one duplicate event.
        new_articles = self.prepare_articles(type='different')
        new_articles = new_articles[:1]

        # Cluster the new duplicate event and raise the min.
        # One cluster should have 3 now and one should have two.
        cluster.cluster(new_articles, min_articles=3)

        # One event should have been deleted.
        self.assertEqual(Event.query.count(), 1)
        self.assertEqual(Event.query.first().members.all(), [articles[0], articles[2], new_articles[0]])
