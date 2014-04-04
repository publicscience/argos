from tests import RequiresDatabase
import tests.factories as fac

from argos.core.models import Story, Event

class StoryTest(RequiresDatabase):
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
