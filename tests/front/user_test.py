from tests import RequiresFront

from argos.web.models.user import User, Auth, AuthExistsForUserException
from argos.datastore import db

class UserTest(RequiresFront):
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
