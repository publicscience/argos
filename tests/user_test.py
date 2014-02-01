from tests import RequiresApp
from models import User, Auth

class UserTest(RequiresApp):
    def setUp(self):
        self.setup_app()

    def tearDown(self):
        self.teardown_app()

    def test_create_or_update_creates(self):
        provider_id = '12e31a'
        provider = 'google'
        data = {
                'name': 'Hubble Bubble',
                'email': 'hubbubs@mail.com',
                'image': 'https://hubb.ub/pic.png'
        }
        user = User.create_or_update(provider_id, provider, '189aec714fad', **data)
        self.assertEqual(Auth.query.count(), 1)
        self.assertEqual(User.query.count(), 1)
        self.assertEqual(Auth.find_by_provider(provider_id, provider).user, user)

    def test_create_or_update_updates(self):
        provider_id = '12e31a'
        provider = 'google'
        access_token = '189aec714fad'
        access_token_ = 'foobar'
        data = {
                'name': 'Hubble Bubble',
                'email': 'hubbubs@mail.com',
                'image': 'https://hubb.ub/pic.png'
        }
        user = User.create_or_update(provider_id, provider, access_token, **data)
        self.assertEqual(Auth.find_by_provider(provider_id, provider).access_token, access_token)
        self.assertEqual(user.name, 'Hubble Bubble')

        data['name'] = 'Bubble Truble'
        user = User.create_or_update(provider_id, provider, access_token_, **data)
        self.assertEqual(Auth.find_by_provider(provider_id, provider).access_token, access_token_)
        self.assertEqual(user.name, 'Bubble Truble')

        self.assertEqual(Auth.query.count(), 1)
        self.assertEqual(User.query.count(), 1)

