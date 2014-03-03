from tests import RequiresApp
import tests.factories as fac
from tests.helpers import save

from argos.web.models.user import User, Auth, AuthExistsForUserException
from argos.web.routes.auth import _process_user
from argos.datastore import db

class UserTest(RequiresApp):
    def setUp(self):
        self.userdata = {
                'name': 'Hubble Bubble',
                'email': 'hubbubs@mail.com',
                'image': 'https://hubb.ub/pic.png'
        }
        self.authdata = {
                'provider': 'google',
                'provider_id': '12e31a',
                'access_token': '18487afkajhsdf'
        }

    def test_add_provider(self):
        user = User(**self.userdata)
        user.add_provider(**self.authdata)

        auth = Auth.for_provider(self.authdata['provider'], self.authdata['provider_id'])

        self.assertEqual(Auth.query.count(), 1)
        self.assertEqual(auth.user, user)

    def test_add_provider_conflict(self):
        auth = Auth(**self.authdata)
        user_a = User(**self.userdata)
        user_b = User(name='Hubble Bubbs')
        auth.user = user_a

        db.session.add(auth)
        db.session.commit()

        self.assertRaises(AuthExistsForUserException, user_b.add_provider, **self.authdata)

    def test_merge(self):
        user_a = User(**self.userdata)
        user_b = User(name='Hubble Bubbs')
        auth_a = Auth(**self.authdata)
        auth_b = Auth('twitter', '8ahf81', '98kn32kafo2')

        auth_a.user = user_a
        auth_b.user = user_b

        for obj in [user_a, user_b, auth_a, auth_b]:
            db.session.add(obj)
        db.session.commit()

        self.assertEqual(User.query.count(), 2)

        user_a.merge(user_b)

        self.assertEqual(len(user_a.auths.all()), 2)
        self.assertEqual(User.query.count(), 1)

    def test_merge_prefer_merger(self):
        user_a = User(**self.userdata)
        user_b = User(name='Hubble Bubbs')
        auth_a = Auth(**self.authdata)
        auth_b = Auth(self.authdata['provider'], '8ahf81', '98kn32kafo2')

        auth_a.user = user_a
        auth_b.user = user_b

        for obj in [user_a, user_b, auth_a, auth_b]:
            db.session.add(obj)
        db.session.commit()

        user_a.merge(user_b)

        self.assertEqual(len(user_a.auths.all()), 1)
        self.assertEqual(user_a.auths.first().provider_id, self.authdata['provider_id'])


class UserAPITest(RequiresApp):
    def setUp(self):
        self.userdata = {
                'name': 'Hubble Bubble',
                'email': 'hubbubs@mail.com',
                'image': 'https://hubb.ub/pic.png',
                'password': '123456'
        }

    def test_get_current_user_not_authenticated(self):
        r = self.client.get('/user')
        self.assertEqual(r.status_code, 401)

    def test_get_current_user_authenticated(self):
        user = User(active=True, **self.userdata)
        self.db.session.add(user)
        self.db.session.commit()
        self.client.post('/test_login', data={'id': 1})
        r = self.client.get('/user')
        self.assertEqual(r.status_code, 200)

    def test_patch_current_user_not_authenticated(self):
        r = self.client.patch('/user', data={'something':'foo'})
        self.assertEqual(r.status_code, 401)

    def test_patch_current_user_authenticated(self):
        user = User(active=True, **self.userdata)
        self.db.session.add(user)
        self.db.session.commit()
        self.client.post('/test_login', data={'id': 1})
        r = self.client.patch('/user', data={'something':'foo'})
        self.assertEqual(r.status_code, 200)

    def test_get_single_user(self):
        user = User(**self.userdata)
        self.db.session.add(user)
        self.db.session.commit()
        r = self.client.get('/users/1')
        self.assertEqual(self.json(r)['name'], self.userdata['name'])

    def test_get_current_user_watching(self):
        user = User(active=True, **self.userdata)
        self.db.session.add(user)

        story = fac.story()
        user.watching.append(story)
        save()

        self.client.post('/test_login', data={'id': 1})

        r = self.client.get('/user/watching')

        expected_members = []
        entities = []
        expected_watchers = [{'url': '/users/{0}'.format(user.id)}]
        for member in story.members:
            expected_members.append({
                'url': '/events/{0}'.format(member.id)
            })
            for entity in member.entities:
                entities.append({
                    'url': '/entities/{0}'.format(entity.slug)
                })

        # Filter down to unique entities.
        expected_entities = list({v['url']:v for v in entities}.values())

        expected = {
                'id': story.id,
                'url': '/stories/{0}'.format(story.id),
                'title': story.title,
                'summary': story.summary,
                'image': story.image,
                'updated_at': story.updated_at.isoformat(),
                'created_at': story.created_at.isoformat(),
                'events': expected_members,
                'entities': expected_entities,
                'watchers': expected_watchers
        }
        self.assertEqual(self.json(r), [expected])

    def test_patch_current_user_watching(self):
        user = User(active=True, **self.userdata)
        self.db.session.add(user)
        story = fac.story()
        save()

        self.client.post('/test_login', data={'id': 1})
        r = self.client.post('/user/watching', data={'story_id':story.id})
        self.assertEqual(r.status_code, 200)
        self.assertEqual(story.watchers, [user])
        self.assertEqual(user.watching, [story])

    def test_delete_current_user_watching(self):
        user = User(active=True, **self.userdata)
        self.db.session.add(user)
        story = fac.story()
        user.watching.append(story)
        save()
        self.client.post('/test_login', data={'id': 1})
        r = self.client.delete('/user/watching?story_id={0}'.format(story.id))
        self.assertEqual(r.status_code, 200)
        self.assertEqual(story.watchers, [])
        self.assertEqual(user.watching, [])

    def test_patch_current_user_watching_not_authenticated(self):
        user = User(active=True, **self.userdata)
        self.db.session.add(user)
        story = fac.story()
        save()

        r = self.client.post('/user/watching', data={'story_id':story.id})
        self.assertEqual(r.status_code, 401)
        self.assertEqual(story.watchers, [])
        self.assertEqual(user.watching, [])

class AuthTest(RequiresApp):
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
