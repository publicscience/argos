import tests.factories as fac
from tests.helpers import save

from tests import RequiresApp

class SearchTest(RequiresApp):
    def test_no_query(self):
        r = self.client.get('/search')
        self.assertEqual(r.status_code, 404)

    def test_simple(self):
        event = fac.event()
        event.title = "Foo bar hey"
        save()

        r = self.client.get('/search/foo')
        data = self.json(r)

        expected = {
            'id': event.id,
            'title': event.title,
            'name': None,
            'slug': None,
            'rank': '0.0',
            'image': event.image,
            'summary': event.summary,
            'updated_at': event.updated_at.isoformat(),
            'created_at': event.created_at.isoformat(),
            'type': 'event',
            'url': '/events/{0}'.format(event.id)
        }

        self.assertEqual(data['pagination']['total_count'], 1)
        self.assertEqual(data['results'], [expected])

    def test_different_types(self):
        event = fac.event()
        event.title = "Foo bar hey"
        save()

        story = fac.story()
        story.title = "Hey there foo foo foo"
        story.summary = "foo foo foo foo foo"
        save()

        r = self.client.get('/search/foo')
        data = self.json(r)

        expected_event = {
            'id': event.id,
            'title': event.title,
            'image': event.image,
            'name': None,
            'slug': None,
            'rank': '0.0',
            'summary': event.summary,
            'updated_at': event.updated_at.isoformat(),
            'created_at': event.created_at.isoformat(),
            'type': 'event',
            'url': '/events/{0}'.format(event.id)
        }

        expected_story = {
            'id': story.id,
            'title': story.title,
            'image': story.image,
            'name': None,
            'slug': None,
            'rank': '0.5',
            'summary': story.summary,
            'updated_at': story.updated_at.isoformat(),
            'created_at': story.created_at.isoformat(),
            'type': 'story',
            'url': '/stories/{0}'.format(story.id)
        }

        self.assertEqual(data['pagination']['total_count'], 2)
        self.assertEqual(data['results'], [expected_story, expected_event])

    def test_only_specified_types(self):
        event = fac.event()
        event.title = "Foo bar hey"
        save()

        story = fac.story()
        story.title = "Hey there foo foo foo"
        save()

        r = self.client.get('/search/foo?types=story')
        data = self.json(r)

        expected_story = {
            'id': story.id,
            'title': story.title,
            'image': story.image,
            'name': None,
            'slug': None,
            'rank': '0.0',
            'summary': story.summary,
            'updated_at': story.updated_at.isoformat(),
            'created_at': story.created_at.isoformat(),
            'type': 'story',
            'url': '/stories/{0}'.format(story.id)
        }

        self.assertEqual(data['pagination']['total_count'], 1)
        self.assertEqual(data['results'], [expected_story])

    def test_only_specified_types_multiple(self):
        event = fac.event()
        event.title = "Foo bar hey"
        save()

        story = fac.story()
        story.title = "Hey there foo"
        save()

        r = self.client.get('/search/foo?types=story,event')
        data = self.json(r)

        expected_event = {
            'id': event.id,
            'title': event.title,
            'image': event.image,
            'name': None,
            'slug': None,
            'rank': '0.0',
            'summary': event.summary,
            'updated_at': event.updated_at.isoformat(),
            'created_at': event.created_at.isoformat(),
            'type': 'event',
            'url': '/events/{0}'.format(event.id)
        }

        expected_story = {
            'id': story.id,
            'title': story.title,
            'image': story.image,
            'name': None,
            'slug': None,
            'rank': '0.0',
            'summary': story.summary,
            'updated_at': story.updated_at.isoformat(),
            'created_at': story.created_at.isoformat(),
            'type': 'story',
            'url': '/stories/{0}'.format(story.id)
        }

        self.assertEqual(data['pagination']['total_count'], 2)
        self.assertEqual(data['results'], [expected_event, expected_story])

    def test_pagination(self):
        events = fac.event(num=20)
        for event in events:
            event.title = "Foo bar hey"
            event.summary = "foo foo foo foo foo"

        stories = fac.story(num=20)
        for story in stories:
            story.title = "Hey there foo"
            story.summary = "foo foo foo foo foo"
        save()

        r = self.client.get('/search/foo')
        data = self.json(r)

        self.assertEqual(data['pagination']['total_count'], 40)
        self.assertEqual(len(data['results']), 20)

    def test_ranking(self):
        event = fac.event()
        event.title = "Foo bar hey"
        event.summary = "bar bar bar bar bar"

        story = fac.story()
        story.title = "Hey there foo"
        story.summary = "foo foo foo foo foo"
        save()

        r = self.client.get('/search/foo')
        data = self.json(r)

        self.assertEqual(data['results'][0]['title'], story.title)
