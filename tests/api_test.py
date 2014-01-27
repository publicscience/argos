from tests import RequiresApp
from json import loads
from models import Entity, Article, Cluster

class ApiTest(RequiresApp):
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
        entity = Entity(name='Horse')
        self.db.session.add(entity)
        self.db.session.commit()
        r = self.app.get('/entities/horse')
        expected = {
                'name': 'Horse',
                'slug': 'horse'
        }
        self.assertEqual(self.data(r), expected)

    def test_GET_event(self):
        members = [
            Article(title='Horses', text='Horses are really neat, Santa'),
            Article(title='Mudcrabs', text='Mudcrabs are everywhere, Bond')
        ]
        event = Cluster(members, tag='event')
        for i in members + [event]:
            self.db.session.add(i)
        self.db.session.commit()

        expected_members = [{
            'type': 'article',
            'title': member.title,
            'id': member.id,
            'url': member.url,
            'created_at': member.created_at.isoformat()
        } for member in members]

        expected_entities = [{
            'name': 'Santa',
            'url': '/entities/santa'
        }, {
            'name': 'Bond',
            'url': '/entities/bond'
        }]

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
        members = [
            Article(title='Horses', text='Horses are really neat, Santa'),
            Article(title='Mudcrabs', text='Mudcrabs are everywhere, Bond')
        ]
        event = Cluster(members, tag='event')
        story = Cluster([event], tag='story')

        for i in members + [event, story]:
            self.db.session.add(i)
        self.db.session.commit()

        expected_members = [{
            'type': 'cluster',
            'title': event.title,
            'id': event.id,
            'url': '/events/%s' % event.id,
            'created_at': event.created_at.isoformat()
        }]

        expected_entities = [{
            'name': 'Santa',
            'url': '/entities/santa'
        }, {
            'name': 'Bond',
            'url': '/entities/bond'
        }]

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
