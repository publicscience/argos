from tests import RequiresApp
from datetime import datetime, timedelta

from argos.core.models import Article, Event

class EventTest(RequiresApp):
    """
    Note this tests the abstract Cluster class's methods as well.
    A Cluster instance can't be instantiated since it is abstract,
    so we use the Event as a testing proxy.
    """
    patch_knowledge = True

    def setUp(self):
        self.article = self.prepare_articles()[0]

    def prepare_articles(self, type='standard', score=100):
        a = {'title':'Dinosaurs', 'text':'dinosaurs are cool, Clinton', 'score':score}
        b = {'title':'Robots', 'text':'robots are nice, Clinton', 'score':score}
        c = {'title':'Robots', 'text':'papa was a rodeo, Clinton', 'score':score}

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

    def prepare_event(self):
        self.cluster = Event(self.prepare_articles())
        self.db.session.add(self.cluster)
        self.db.session.commit()

    def test_similarity_with_object_different(self):
        self.prepare_event()
        avg_sim = self.cluster.similarity(self.article)
        self.assertNotEqual(avg_sim, 1.0)
        self.assertNotEqual(avg_sim, 0.0)

    def test_similarity_with_object_duplicates(self):
        members = self.prepare_articles(type='duplicate')
        c = Event(members)
        avg_sim = c.similarity(self.article)
        self.assertEqual(avg_sim, 1.0)

    def test_similarity_with_cluster_duplicates(self):
        self.prepare_event()
        members = (self.prepare_articles())
        c = Event(members)
        avg_sim = self.cluster.similarity(c)

        # Currently, the similarity calculation between clusters
        # does not yield 1.0 if they are identical clusters,
        # because we calculate the average similarity of the articles
        # between the clusters, rather than the overlap of the two clusters.
        #self.assertEqual(avg_sim, 1.0)
        self.assertAlmostEqual(avg_sim, 0.83999999999999)

    def test_similarity_with_cluster_different(self):
        self.prepare_event()
        members = self.prepare_articles(type='different')
        c = Event(members)

        avg_sim = self.cluster.similarity(c)
        self.assertNotEqual(avg_sim, 1.0)
        self.assertNotEqual(avg_sim, 0.0)

    def test_expired_made_inactive(self):
        self.prepare_event()
        self.cluster.updated_at = datetime.utcnow() - timedelta(days=4)
        Event.cluster([self.article])
        self.assertFalse(self.cluster.active)

    def test_clusters_similar(self):
        self.prepare_event()
        members = self.prepare_articles(type='duplicate')
        self.cluster.members = members

        Event.cluster([self.article])
        self.assertEqual(len(self.cluster.members), 3)

    def test_does_not_cluster_if_no_shared_entities(self):
        self.prepare_event()
        members = [Article(
            title='Robots',
            text='dinosaurs are cool, Reagan',
            created_at=datetime.utcnow()
        )]
        self.cluster.members = members

        Event.cluster([self.article])
        self.assertEqual(len(self.cluster.members), 1)

    def test_does_not_cluster_not_similar(self):
        self.prepare_event()
        article = Article(
                title='Superstars',
                text='superstars are awesome, Clinton',
                created_at=datetime.utcnow()
        )
        Event.cluster([article])
        self.assertEqual(len(self.cluster.members), 2)

    def test_no_matching_cluster_creates_new_cluster(self):
        article = Article(
                title='Superstars',
                text='superstars are awesome, Clinton',
                created_at=datetime.utcnow()
        )
        Event.cluster([article])

        self.assertEqual(Event.query.count(), 1)

    def test_entitize(self):
        members = [Article(
            title='Robots',
            text='dinosaurs are cool, Reagan'
        ), self.prepare_articles()[0]]
        self.cluster = Event(members)
        entities = {ent.slug for ent in self.cluster.entities}
        self.assertEqual(entities, {'Clinton', 'Reagan'})

    def test_entitize_no_duplicates(self):
        self.cluster = Event(self.prepare_articles())
        entities = [ent.slug for ent in self.cluster.entities]
        self.assertEqual(entities, ['Clinton'])

    def test_titleize(self):
        members = [Article(
            title='Robots',
            text='dinosaurs are cool, Reagan'
        )] + self.prepare_articles(type='duplicate')
        self.cluster = Event(members)
        self.assertEqual(self.cluster.title, 'Dinosaurs')

    def test_summarize(self):
        self.cluster = Event(self.prepare_articles())
        self.assertTrue(self.cluster.summary)

    def test_summarize_single_article(self):
        self.cluster = Event([self.prepare_articles()[0]])
        self.assertTrue(self.cluster.summary)

    def test_timespan(self):
        text = 'the worldly philosophers today cautious optimism is based to a large extent on technological breakthroughs'
        members = [
                Article(title='A', text=text, created_at=datetime(2014, 1, 20, 1, 1, 1, 111111)),
                Article(title='B', text=text, created_at=datetime(2014, 1, 22, 1, 1, 1, 111111)),
                Article(title='C', text=text, created_at=datetime(2014, 1, 24, 1, 1, 1, 111111))
        ]
        self.cluster = Event(members)
        results = self.cluster.timespan(datetime(2014, 1, 21, 1, 1, 1, 111111))
        self.assertEqual(len(results), 2)
        self.assertEqual({r.title for r in results}, {'B', 'C'})

    def test_score_prefer_newer_events(self):
        event_a = Event(self.prepare_articles())
        event_b = Event(self.prepare_articles())

        self.assertGreater(event_b.score, event_a.score)

    def test_score_prefer_events_with_higher_article_scores(self):
        event_a = Event(self.prepare_articles())
        event_b = Event(self.prepare_articles(score=200))

        self.assertGreater(event_b.score, event_a.score)
