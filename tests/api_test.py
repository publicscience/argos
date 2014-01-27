from tests import RequiresApp
import tests.factories as fac
from json import loads
from models import Entity, Article, Cluster

class APITest(RequiresApp):
    def setUp(self):
        self.setup_app()

    def tearDown(self):
        self.teardown_app()

    def data(self, resp):
        """
        Load response data into json.
        """
        return loads(resp.data.decode('utf-8'))

    def test_404(self):
        r = self.app.get('/does_not_exist')
        self.assertTrue(r.data)
        self.assertEquals(r.status_code, 404)

    def test_GET_entity(self):
        entity = fac.entity()
        r = self.app.get('/entities/%s' % entity.slug)
        expected = {
                'name': entity.name,
                'slug': entity.slug
        }
        self.assertEqual(self.data(r), expected)

    def test_GET_event(self):
        event = fac.event()

        expected_members = []
        entities = []
        for member in event.members:
            expected_members.append({
                'type': 'article',
                'title': member.title,
                'id': member.id,
                'url': member.url,
                'created_at': member.created_at.isoformat()
            })
            for entity in member.entities:
                entities.append({
                    'name': entity.name,
                    'url': '/entities/%s' % entity.slug
                })

        # Filter down to unique entities.
        expected_entities = list({v['url']:v for v in entities}.values())

        expected = {
                'id': event.id,
                'title': event.title,
                'summary': event.summary,
                'tag': event.tag,
                'updated_at': event.updated_at.isoformat(),
                'created_at': event.created_at.isoformat(),
                'members': expected_members,
                'entities': expected_entities
        }

        r = self.app.get('/events/%s' % event.id)

        self.assertEqual(self.data(r), expected)

    def test_GET_story(self):
        story = fac.story()

        expected_members = []
        entities = []
        for member in story.members:
            expected_members.append({
                'type': 'cluster',
                'title': member.title,
                'id': member.id,
                'url': '/events/%s' % member.id,
                'created_at': member.created_at.isoformat()
            })
            for entity in member.entities:
                entities.append({
                    'name': entity.name,
                    'url': '/entities/%s' % entity.slug
                })

        # Filter down to unique entities.
        expected_entities = list({v['url']:v for v in entities}.values())

        expected = {
                'id': story.id,
                'title': story.title,
                'summary': story.summary,
                'tag': story.tag,
                'updated_at': story.updated_at.isoformat(),
                'created_at': story.created_at.isoformat(),
                'members': expected_members,
                'entities': expected_entities
        }

        r = self.app.get('/stories/%s' % story.id)

        self.assertEqual(self.data(r), expected)
