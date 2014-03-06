from tests import RequiresApp
import tests.factories as fac

from argos.core.models import Story, Event

class StoryTest(RequiresApp):
    def test_story_entitize(self):
        story = fac.story()

        expected_entities = []
        for event in story.events:
            expected_entities += [ent.slug for ent in event.entities]

        expected_entities = set(expected_entities)

        entities = {ent.slug for ent in story.entities}
        self.assertEqual(entities, expected_entities)

    def test_story_clustering_with_matching_entities(self):
        # This creates a story with duplicate member events.
        story = fac.story()

        # This event is a duplicate of the story's events.
        event = fac.event()

        Story.cluster([event])
        self.assertEqual(len(story.members), 3)

    def test_story_clustering_without_matching_entities(self):
        story = fac.story()

        # Create an event with completely different entities
        # from the story.
        article = fac.article(title='The Illiad', text='The Illiad has Argos in it.')
        event = Event([article])

        Story.cluster([event])
        self.assertEqual(len(story.members), 2)
        self.assertEqual(Story.query.count(), 2)

    def test_story_summarize(self):
        story = fac.story()
        self.assertTrue(story.summary)
