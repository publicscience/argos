from tests import RequiresApp

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
                'provider_id': '12e31a',
                'provider': 'google',
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
        r = self.client.post('/test_login', data={'id': 1})
        r = self.client.get('/user')
        self.assertEqual(r.status_code, 200)

    def test_patch_current_user_not_authenticated(self):
        r = self.client.patch('/user', data={'something':'foo'})
        self.assertEqual(r.status_code, 401)

    def test_patch_current_user_authenticated(self):
        user = User(active=True, **self.userdata)
        self.db.session.add(user)
        self.db.session.commit()
        r = self.client.post('/test_login', data={'id': 1})
        r = self.client.patch('/user', data={'something':'foo'})
        self.assertEqual(r.status_code, 200)

    def test_get_single_user(self):
        user = User(**self.userdata)
        self.db.session.add(user)
        self.db.session.commit()
        r = self.client.get('/users/1')
        self.assertEqual(self.json(r)['name'], self.userdata['name'])

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
