from tests import RequiresDatabase
from datetime import datetime, timedelta

from argos.core.models import Article, Event, Source

class EventTest(RequiresDatabase):
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

        # Need to save these articles to persist concepts,
        # so that their overlaps are calculated properly when clustering!
        for article in articles:
            self.db.session.add(article)
        self.db.session.commit()

        return articles

    def prepare_event(self):
        self.event = Event(self.prepare_articles())
        self.db.session.add(self.event)
        self.db.session.commit()

    def test_event_deletion_removes_from_articles_events(self):
        articles = self.prepare_articles()
        for article in articles:
            self.db.session.add(article)

        # Make an event.
        self.event = Event(articles)
        self.db.session.add(self.event)
        self.db.session.commit()

        # The articles should reference their events.
        for article in articles:
            self.assertEqual(article.events, [self.event])

        # Destroy events.
        Event.query.delete()
        self.db.session.commit()

        # The articles should no longer have references to the events.
        for article in articles:
            self.assertEqual(article.events, [])

    def test_conceptize(self):
        members = [Article(
            title='Robots',
            text='dinosaurs are cool, Reagan'
        ), self.prepare_articles()[0]]
        self.event = Event(members)

        concepts = {con.slug for con in self.event.concepts}
        mentions = {ali.name for ali in self.event.mentions}

        self.assertEqual(concepts, {'Clinton', 'Reagan'})
        self.assertEqual(mentions, {'Clinton', 'Reagan'})

        # Each concept's score won't be 0.5, since
        # they are weighed down by the commonness.
        for concept in self.event.concepts:
            self.assertAlmostEqual(concept.score, 0.005, places=3)

    def test_conceptize_no_duplicates(self):
        self.event = Event(self.prepare_articles())
        concepts = [con.slug for con in self.event.concepts]
        mentions = [ali.name for ali in self.event.mentions]
        self.assertEqual(concepts, ['Clinton'])
        self.assertEqual(mentions, ['Clinton'])

    def test_summarize(self):
        self.event = Event(self.prepare_articles())
        self.assertTrue(self.event.summary)

    def test_summarize_single_article(self):
        self.event = Event([self.prepare_articles()[0]])
        self.assertTrue(self.event.summary)

    def test_summary_sentences(self):
        # Check to see that we can break up the summary
        # back into its original sentences.

        from argos.core.brain import summarizer
        title = 'Syria Misses New Deadline as It Works to Purge Arms'
        text = 'Syria missed a revised deadline on Sunday for completing the export or destruction of chemicals in its weapons arsenal, but the government of the war-ravaged country may be only days away from finishing the job, according to international experts overseeing the process. The Syrian government had agreed to complete the export or destruction of about 1,200 tons of chemical agents by April 27 after missing a February deadline, but by Sunday, it had shipped out or destroyed 92.5 percent of the arsenal, said Sigrid Kaag, the coordinator of the joint mission by the United Nations and the watchdog agency the Organization for the Prohibition of Chemical Weapons.'
        expected_sents = summarizer.summarize(title, text)

        source = Source()
        source.name = 'Super Cool Times'

        article = Article(
                        title=title,
                        text=text,
                        score=100)
        article.source = source
        article.ext_url = 'http://foo.com'

        self.event=Event([article])

        expected = [{
            'sentence': sent,
            'source': 'Super Cool Times',
            'url': 'http://foo.com'
        } for sent in expected_sents]

        self.assertEqual(self.event.summary_sentences, expected)

    def test_timespan(self):
        text = 'the worldly philosophers today cautious optimism is based to a large extent on technological breakthroughs'
        members = [
                Article(title='A', text=text, created_at=datetime(2014, 1, 20, 1, 1, 1, 111111)),
                Article(title='B', text=text, created_at=datetime(2014, 1, 22, 1, 1, 1, 111111)),
                Article(title='C', text=text, created_at=datetime(2014, 1, 24, 1, 1, 1, 111111))
        ]
        self.event = Event(members)
        results = self.event.timespan(datetime(2014, 1, 21, 1, 1, 1, 111111))
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
