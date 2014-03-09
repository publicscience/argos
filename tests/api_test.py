import tests.factories as fac
from tests.helpers import save

from tests import RequiresApp

class APITest(RequiresApp):
    def test_404(self):
        r = self.client.get('/does_not_exist')
        self.assertTrue(r.data)
        self.assertEqual(r.status_code, 404)

    def test_GET_entity(self):
        entity = fac.entity()
        r = self.client.get('/entities/{0}'.format(entity.slug))
        expected = {
                'name': entity.name,
                'names': entity.names,
                'slug': entity.slug,
                'url': '/entities/{0}'.format(entity.slug),
                'updated_at': entity.updated_at.isoformat(),
                'summary': entity.summary,
                'image': entity.image,
                'stories': []
        }
        self.assertEqual(self.json(r), expected)

    def test_GET_event(self):
        # The score of an event is hard to anticipate, so mock it.
        self.create_patch('argos.core.models.Event.score', return_value=1.0)

        event = fac.event()
        event.members[0].image = 'http://foo.jpg'
        event.members[1].image = 'http://foo2.jpg'
        save()

        expected_members = []
        expected_entities = [{'url': '/entities/{0}'.format(entity.slug)} for entity in event.entities]
        expected_mentions = [{'name': alias.name, 'slug': alias.entity.slug} for alias in event.mentions]
        for member in event.members:
            expected_members.append({
                'url': '/articles/{0}'.format(member.id)
            })

        expected = {
                'id': event.id,
                'url': '/events/{0}'.format(event.id),
                'title': event.title,
                'summary': event.summary,
                'image': event.image,
                'images': ['http://foo.jpg', 'http://foo2.jpg'],
                'score': '1.0', # json returns floats as strings.
                'updated_at': event.updated_at.isoformat(),
                'created_at': event.created_at.isoformat(),
                'articles': expected_members,
                'entities': expected_entities,
                'mentions': expected_mentions,
                'stories': []
        }

        r = self.client.get('/events/{0}'.format(event.id))

        self.assertEqual(self.json(r), expected)

    def test_GET_story(self):
        story = fac.story()
        users = fac.user(num=4)
        story.watchers = users
        story.members[0].image = 'http://foo.jpg'
        story.members[1].image = 'http://foo2.jpg'
        save()

        expected_members = []
        expected_watchers = []
        expected_entities = [{'url': '/entities/{0}'.format(entity.slug)} for entity in story.entities]
        expected_mentions = [{'name': alias.name, 'slug': alias.entity.slug} for alias in story.mentions]
        for member in story.members:
            expected_members.append({
                'url': '/events/{0}'.format(member.id)
            })
        for user in users:
            expected_watchers.append({
                'url': '/users/{0}'.format(user.id)
            })

        expected = {
                'id': story.id,
                'url': '/stories/{0}'.format(story.id),
                'title': story.title,
                'summary': story.summary,
                'image': story.image,
                'images': ['http://foo.jpg', 'http://foo2.jpg'],
                'updated_at': story.updated_at.isoformat(),
                'created_at': story.created_at.isoformat(),
                'events': expected_members,
                'entities': expected_entities,
                'mentions': expected_mentions,
                'watchers': expected_watchers
        }

        r = self.client.get('/stories/{0}'.format(story.id))

        self.assertEqual(self.json(r), expected)

    def test_GET_story_watchers(self):
        story = fac.story()
        users = fac.user(num=3)
        story.watchers = users
        save()

        expected = []
        for user in users:
            expected.append({
                'id': user.id,
                'name': user.name,
                'image': user.image,
                'created_at': user.created_at.isoformat(),
                'updated_at': user.updated_at.isoformat()
            })

        r = self.client.get('/stories/{0}/watchers'.format(story.id))

        self.assertEqual(self.json(r), expected)

    def test_POST_story_watchers(self):
        story = fac.story()
        users = fac.user(num=4)
        user = users[-1]
        story.watchers = users[:3]
        save()

        self.assertEqual(len(story.watchers), 3)

        # Login the user so we have an authenticated user.
        r = self.client.post('/test_login', data={'id': user.id})

        r = self.client.post('/stories/{0}/watchers'.format(story.id))
        self.assertEqual(len(story.watchers), 4)

    def test_DELETE_story_watchers(self):
        story = fac.story()
        users = fac.user(num=3)
        user = users[0]
        story.watchers = users
        save()

        self.assertEqual(len(story.watchers), 3)

        # Login the user so we have an authenticated user.
        r = self.client.post('/test_login', data={'id': user.id})

        r = self.client.delete('/stories/{0}/watchers'.format(story.id))
        self.assertEqual(len(story.watchers), 2)
        for watcher in story.watchers:
            self.assertNotEqual(watcher, user)

    def test_GET_article(self):
        article = fac.article()
        source = fac.source()
        article.source = source
        save()

        r = self.client.get('/articles/{0}'.format(article.id))
        expected = {
                'id': article.id,
                'url': '/articles/{0}'.format(article.id),
                'title': article.title,
                'ext_url': article.ext_url,
                'image': article.image,
                'created_at': article.created_at.isoformat(),
                'updated_at': article.updated_at.isoformat(),
                'authors': [],
                'events': [],
                'source': {
                    'url': '/sources/{0}'.format(source.id),
                    'name': source.name
                }
        }
        self.assertEqual(self.json(r), expected)

    def test_GET_trending(self):
        events = sorted([fac.event(),
                        fac.event(),
                        fac.event()],
                        key=lambda x: x.score,
                        reverse=True)
        event_ids = [event.id for event in events]
        r = self.client.get('/trending')
        self.assertEqual([event['id'] for event in self.json(r)], event_ids)

