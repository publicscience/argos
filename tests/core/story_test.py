from tests import RequiresDatabase
import tests.factories as fac

from datetime import datetime, timedelta

from argos.core.models import Story, Event

class StoryTest(RequiresDatabase):
    def _create_dated_story(self):
        datetime_A = datetime.utcnow() - timedelta(days=1)
        datetime_B = datetime.utcnow() - timedelta(days=5)

        article_a = fac.article(title='The Illiad', text='The Illiad has Argos in it.')
        event_a = Event([article_a])
        event_a.created_at = datetime_A

        article_b = fac.article(title='The Illiad', text='The Illiad has Argos in it.')
        event_b = Event([article_b])
        event_b.created_at = datetime_B

        article_c = fac.article(title='The Illiad', text='The Illiad has Argos in it.')
        event_c = Event([article_c])
        event_c.created_at = datetime_A

        story = Story([event_a, event_b, event_c])

        self.db.session.add(story)
        self.db.session.commit()

        return story, datetime_A, datetime_B

    def test_story_conceptize(self):
        story = fac.story()

        expected_concepts = []
        expected_mentions = []
        for event in story.events:
            expected_concepts += [con.slug for con in event.concepts]
            expected_mentions += [ali.name for ali in event.mentions]

        expected_concepts = set(expected_concepts)
        expected_mentions = set(expected_mentions)

        concepts = {con.slug for con in story.concepts}
        mentions = {ali.name for ali in story.mentions}
        self.assertEqual(concepts, expected_concepts)
        self.assertEqual(mentions, expected_mentions)

    def test_story_clustering_with_matching_concepts(self):
        # This creates a story with duplicate member events.
        story = fac.story()

        # This event is a duplicate of the story's events.
        event = fac.event()

        Story.cluster([event])
        self.assertEqual(story.members.count(), 3)

    def test_story_clustering_without_matching_concepts(self):
        story = fac.story()

        # Create an event with completely different concepts
        # from the story.
        article = fac.article(title='The Illiad', text='The Illiad has Argos in it.')
        event = Event([article])

        Story.cluster([event])
        self.assertEqual(story.members.count(), 2)
        self.assertEqual(Story.query.count(), 2)

    def test_story_summarize(self):
        story = fac.story()
        self.assertTrue(story.summary)

    def test_story_events_by_date(self):
        story, datetime_A, datetime_B = self._create_dated_story()

        groups = story.events_by_date()
        self.assertEqual(groups[0][0], datetime_A.date())
        self.assertEqual(len(groups[0][1]), 2)

        self.assertEqual(groups[1][0], datetime_B.date())
        self.assertEqual(len(groups[1][1]), 1)

    def test_story_events_before(self):
        story, datetime_A, datetime_B = self._create_dated_story()

        # Set the datetime to be *after* datetime_B so events
        # created at datetime_B come before. So we expect them as results.
        events = story.events_before(datetime_B + timedelta(days=1))
        self.assertEqual(len(events), 1)

        # We expect all events now since they are all before 100 days from now.
        events = story.events_before(datetime_A + timedelta(days=100))
        self.assertEqual(len(events), 3)

    def test_story_events_after(self):
        story, datetime_A, datetime_B = self._create_dated_story()

        # Set the datetime to be *before* datetime_A so events
        # created at datetime_A come after. So we expect them as results.
        events = story.events_after(datetime_A - timedelta(days=1))
        self.assertEqual(len(events), 2)

        # We expect all events now since they are all after 100 days ago.
        events = story.events_after(datetime_B - timedelta(days=100))
        self.assertEqual(len(events), 3)

    def test_recluster(self):
        # Doesn't matter what the article text is, since the knowledge module is patched
        # to return the same concepts regardless.
        article_a = fac.article(title='The Illiad', text='The Illiad has Argos in it.')
        event_a = Event([article_a])
        self.db.session.add(event_a)

        article_b = fac.article(title='The Illiad', text='The Illiad has Argos in it.')
        event_b = Event([article_b])
        self.db.session.add(event_b)

        events = [event_a, event_b]

        Story.cluster(events, threshold=0.0)
        self.assertEqual(Story.query.count(), 1)

        original_id = Story.query.first().id

        # The original story should be deleted,
        # and now we should have two new stories.
        Story.recluster(events, threshold=1.0)
        self.assertEqual(Story.query.get(original_id), None)
        self.assertEqual(Story.query.count(), 2)
