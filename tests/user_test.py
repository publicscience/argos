from tests import RequiresApp
from models import User, Auth
from flask_security.utils import login_user
from flask_security.core import current_user

class UserTest(RequiresApp):
    def setUp(self):
        self.setup_app()
        self.userdata = {
                'name': 'Hubble Bubble',
                'email': 'hubbubs@mail.com',
                'image': 'https://hubb.ub/pic.png'
        }

    def tearDown(self):
        self.teardown_app()

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
        self.setup_app()
        self.userdata = {
                'name': 'Hubble Bubble',
                'email': 'hubbubs@mail.com',
                'image': 'https://hubb.ub/pic.png'
        }

    def tearDown(self):
        self.teardown_app()

    def test_get_current_user_not_authenticated(self):
        r = self.app.get('/user')
        self.assertEqual(self.data(r)['status'], 401)

    def test_get_current_user_authenticated(self):
        with self.app_context() as c:
            user = User(active=True, **self.userdata)
            self.db.session.add(user)
            self.db.session.commit()
            login_user(user)
            r = c.get('/user')
            self.assertEqual(self.data(r)['status'], 401)
