from tests import RequiresApp

from web.models import User, Auth

class UserTest(RequiresApp):
    def setUp(self):
        self.userdata = {
                'name': 'Hubble Bubble',
                'email': 'hubbubs@mail.com',
                'image': 'https://hubb.ub/pic.png'
        }

    def test_create_or_update_creates(self):
        provider_id = '12e31a'
        provider = 'google'
        user = User.create_or_update(provider_id, provider, '189aec714fad', **self.userdata)
        self.assertEqual(Auth.query.count(), 1)
        self.assertEqual(User.query.count(), 1)
        self.assertEqual(Auth.find_by_provider(provider_id, provider).user, user)

    def test_create_or_update_updates(self):
        provider_id = '12e31a'
        provider = 'google'
        access_token = '189aec714fad'
        access_token_ = 'foobar'
        user = User.create_or_update(provider_id, provider, access_token, **self.userdata)
        self.assertEqual(Auth.find_by_provider(provider_id, provider).access_token, access_token)
        self.assertEqual(user.name, 'Hubble Bubble')

        self.userdata['name'] = 'Bubble Truble'
        user = User.create_or_update(provider_id, provider, access_token_, **self.userdata)
        self.assertEqual(Auth.find_by_provider(provider_id, provider).access_token, access_token_)
        self.assertEqual(user.name, 'Bubble Truble')

        self.assertEqual(Auth.query.count(), 1)
        self.assertEqual(User.query.count(), 1)

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
        # login user?
        r = self.client.get('/user')
        self.assertEqual(r.status_code, 200)

    def test_patch_current_user_not_authenticated(self):
        r = self.client.patch('/user', data={'something':'foo'})
        self.assertEqual(r.status_code, 401)

    def test_patch_current_user_authenticated(self):
        user = User(active=True, **self.userdata)
        self.db.session.add(user)
        self.db.session.commit()
        # login user?
        # this should be an actual attribute on the user
        r = self.client.patch('/user', data={'something':'foo'})
        self.assertEqual(r.status_code, 200)

    def test_get_single_user(self):
        user = User(**self.userdata)
        self.db.session.add(user)
        self.db.session.commit()
        r = self.client.get('/users/1')
        self.assertEqual(self.json(r)['name'], self.userdata['name'])
