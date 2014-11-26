from tests import RequiresAPI
import tests.factories as fac
from tests.helpers import save

from argos.web.models.user import User, Auth
from argos.datastore import db

class UserAPITest(RequiresAPI):
    def setUp(self):
        self.userdata = {
                'name': 'Hubble Bubble',
                'email': 'hubbubs@mail.com',
                'image': 'https://hubb.ub/pic.png',
                'password': '123456'
        }

    def token(self):
        # Get a token for authenticated API requests.
        r = self.client.post('/test_auth', data={'id': 1})
        return self.json(r)['token']

    def auth_get(self, endpoint):
        token = self.token()
        return self.client.get(
                endpoint,
                headers={'Authorization': 'Bearer {0}'.format(token)})

    def auth_delete(self, endpoint):
        token = self.token()
        return self.client.delete(
                endpoint,
                headers={'Authorization': 'Bearer {0}'.format(token)})

    def auth_patch(self, endpoint, data):
        token = self.token()
        return self.client.patch(
                endpoint,
                headers={'Authorization': 'Bearer {0}'.format(token)},
                data=data)

    def auth_post(self, endpoint, data):
        token = self.token()
        return self.client.post(
                endpoint,
                headers={'Authorization': 'Bearer {0}'.format(token)},
                data=data)

    def test_get_current_user_not_authenticated(self):
        r = self.client.get('/user')
        self.assertEqual(r.status_code, 401)

    def test_get_current_user_authenticated(self):
        user = User(active=True, **self.userdata)
        self.db.session.add(user)
        self.db.session.commit()
        r = self.auth_get('/user')
        self.assertEqual(r.status_code, 200)

    def test_patch_current_user_not_authenticated(self):
        r = self.client.patch('/user', data={'something':'foo'})
        self.assertEqual(r.status_code, 401)

    def test_patch_current_user_authenticated(self):
        user = User(active=True, **self.userdata)
        self.db.session.add(user)
        self.db.session.commit()
        r = self.auth_patch('/user', data={'something':'foo'})
        self.assertEqual(r.status_code, 204)

    def test_get_single_user(self):
        user = User(**self.userdata)
        self.db.session.add(user)
        self.db.session.commit()
        r = self.client.get('/users/1')
        self.assertEqual(self.json(r)['name'], self.userdata['name'])

    def test_get_users(self):
        user_a = User(**self.userdata)
        user_b = User(**{
            'name': 'Foo Bar',
            'email': 'foo@foo.com',
            'image': 'https://foob.ar/pic.png',
            'password': '123456'
        })
        self.db.session.add(user_a)
        self.db.session.add(user_b)
        self.db.session.commit()

        r = self.client.get('/users')

        expected_names = [user_a.name, user_b.name]
        data = self.json(r)
        names = [u['name'] for u in data['results']]
        self.assertEqual(expected_names, names)
        self.assertEqual(data['pagination']['total_count'], 2)

    def test_get_current_user_watching(self):
        user = User(active=True, **self.userdata)
        self.db.session.add(user)

        story = fac.story()
        user.watching.append(story)
        save()

        r = self.auth_get('/user/watching')

        expected_members = []
        expected_concepts = [{
            'slug': concept.slug,
            'url': '/concepts/{0}'.format(concept.slug),
            'score': str(1.0/len(story.concepts))
        } for concept in story.concepts]
        expected_watchers = [{'url': '/users/{0}'.format(user.id), 'id': user.id}]
        expected_mentions = [{'name': alias.name, 'slug': alias.concept.slug, 'id': alias.id} for alias in story.mentions]
        for member in story.members:
            expected_members.append({
                'id': member.id,
                'url': '/events/{0}'.format(member.id)
            })

        expected = {
                'id': story.id,
                'url': '/stories/{0}'.format(story.id),
                'title': story.title,
                'summary': story.summary,
                'image': story.image,
                'images': [],
                'updated_at': story.updated_at.isoformat(),
                'created_at': story.created_at.isoformat(),
                'events': expected_members,
                'concepts': expected_concepts,
                'mentions': expected_mentions,
                'watchers': expected_watchers
        }
        self.assertEqual(self.json(r), [expected])

    def test_post_current_user_watching(self):
        user = User(active=True, **self.userdata)
        self.db.session.add(user)
        story = fac.story()
        save()

        r = self.auth_post('/user/watching', data={'story_id':story.id})
        self.assertEqual(r.status_code, 201)
        self.assertEqual(story.watchers, [user])
        self.assertEqual(user.watching, [story])

    def test_delete_current_user_watching(self):
        user = User(active=True, **self.userdata)
        self.db.session.add(user)
        story = fac.story()
        user.watching.append(story)
        save()
        r = self.auth_delete('/user/watching/{0}'.format(story.id))
        self.assertEqual(r.status_code, 204)
        self.assertEqual(story.watchers, [])
        self.assertEqual(user.watching, [])

    def test_post_current_user_watching_not_authenticated(self):
        user = User(active=True, **self.userdata)
        self.db.session.add(user)
        story = fac.story()
        save()

        r = self.client.post('/user/watching', data={'story_id':story.id})
        self.assertEqual(r.status_code, 401)
        self.assertEqual(story.watchers, [])
        self.assertEqual(user.watching, [])

    def test_current_user_check_watching(self):
        user = User(active=True, **self.userdata)
        self.db.session.add(user)

        watched_story = fac.story()
        user.watching.append(watched_story)
        not_watched_story = fac.story()
        save()

        r = self.auth_get('/user/watching/{0}'.format(watched_story.id))
        self.assertEqual(r.status_code, 204)

        r = self.auth_get('/user/watching/{0}'.format(not_watched_story.id))
        self.assertEqual(r.status_code, 404)

    def test_get_current_user_bookmarked(self):
        # The score of an event is hard to anticipate, so mock it.
        self.create_patch('argos.core.models.Event.score', return_value=1.0)

        user = User(active=True, **self.userdata)
        self.db.session.add(user)

        event = fac.event()

        user.bookmarked.append(event)
        save()

        r = self.auth_get('/user/bookmarked')

        expected_members = []
        expected_concepts = [{
            'slug': concept.slug,
            'url': '/concepts/{0}'.format(concept.slug),
            'score': str(1.0/len(event.concepts))
        } for concept in event.concepts]
        expected_mentions = [{'name': alias.name, 'slug': alias.concept.slug, 'id': alias.id} for alias in event.mentions]
        for member in event.members:
            expected_members.append({
                'id': member.id,
                'url': '/articles/{0}'.format(member.id)
            })

        expected = {
                'id': event.id,
                'url': '/events/{0}'.format(event.id),
                'title': event.title,
                'summary': event.summary,
                'image': event.image,
                'images': [],
                'score': '1.0', # json returns floats as strings.
                'updated_at': event.updated_at.isoformat(),
                'created_at': event.created_at.isoformat(),
                'articles': expected_members,
                'concepts': expected_concepts,
                'mentions': expected_mentions,
                'stories': []
        }

        print(self.json(r))
        print('\n\n\n')
        print([expected])

        self.assertEqual(self.json(r), [expected])

    def test_post_current_user_bookmarked(self):
        user = User(active=True, **self.userdata)
        self.db.session.add(user)

        event = fac.event()
        save()

        r = self.auth_post('/user/bookmarked', data={'event_id':event.id})
        self.assertEqual(r.status_code, 201)
        self.assertEqual(user.bookmarked, [event])

    def test_delete_current_user_bookmarked(self):
        user = User(active=True, **self.userdata)
        self.db.session.add(user)
        event = fac.event()
        user.bookmarked.append(event)
        save()
        r = self.auth_delete('/user/bookmarked/{0}'.format(event.id))
        self.assertEqual(r.status_code, 204)
        self.assertEqual(user.bookmarked, [])

    def test_post_current_user_bookmarked_not_authenticated(self):
        user = User(active=True, **self.userdata)
        self.db.session.add(user)

        event = fac.event()
        save()

        r = self.client.post('/user/bookmarked', data={'event_id':event.id})
        self.assertEqual(r.status_code, 401)
        self.assertEqual(user.bookmarked, [])

    def test_current_user_check_bookmarked(self):
        user = User(active=True, **self.userdata)
        self.db.session.add(user)

        bookmarked_event = fac.event()
        user.bookmarked.append(bookmarked_event)
        not_bookmarked_event = fac.event()
        save()

        r = self.auth_get('/user/bookmarked/{0}'.format(bookmarked_event.id))
        self.assertEqual(r.status_code, 204)

        r = self.auth_get('/user/bookmarked/{0}'.format(not_bookmarked_event.id))
        self.assertEqual(r.status_code, 404)

    def test_get_current_user_feed(self):
        user = User(active=True, **self.userdata)
        self.db.session.add(user)

        story = fac.story()
        not_watched_story = fac.story()
        user.watching.append(story)
        save()

        r = self.auth_get('/user/feed')
        expected_event_ids = [event.id for event in story.events]
        not_expected_event_ids = [event.id for event in not_watched_story.events]
        result_event_ids = [event['id'] for event in self.json(r)]
        self.assertEqual(result_event_ids, expected_event_ids)
        self.assertNotEqual(result_event_ids, not_expected_event_ids)


class AuthTest(RequiresAPI):
    def test_update_token_simple(self):
        a = Auth('12345', 'twooter', 'an_access_token')
        a.update_token('new_token')
        self.assertEqual(a.access_token, 'new_token')

    def test_update_token_missing_secret(self):
        secret = 'an_access_token_secret'
        a = Auth('12345', 'twooter', 'an_access_token', secret)
        self.assertRaises(Exception, a.update_token, 'new_token')

    def test_update_token_with_secret(self):
        secret = 'an_access_token_secret'
        a = Auth('12345', 'twooter', 'an_access_token', secret)
        a.update_token('new_token', 'new_secret')
        self.assertEqual(a.access_token, 'new_token')
        self.assertEqual(a.access_token_secret, 'new_secret')

    def test_auth_encrypts_decrypts_secret(self):
        secret = 'an_access_token_secret'
        a = Auth('12345', 'twooter', 'an_access_token', secret)
        self.assertNotEqual(a._access_token_secret, secret)
        self.assertEqual(a.access_token_secret, secret)
        self.db.session.add(a)
        self.db.session.commit()
        self.assertEqual(Auth.query.count(), 1)

        # Test that retrieval/decryption works as expected as well.
        a = None
        a = Auth.query.first()
        self.assertNotEqual(a._access_token_secret, secret)
        self.assertEqual(a.access_token_secret, secret)
