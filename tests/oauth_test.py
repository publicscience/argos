from tests import RequiresApp

from argos.web.models.user import User
from argos.web.models.oauth import Client, Token, Grant
from flask_security.registerable import register_user

from urllib.parse import quote_plus

class OAuthTest(RequiresApp):
    userdata = {
            'name': 'Hubble Bubble',
            'email': 'hubbubs@mail.com',
            'image': 'https://hubb.ub/pic.png',
            'password': '123456'
    }
    default_redirect_uri = 'http://localhost:5000/authorized'
    encoded_redirect_uri = quote_plus(default_redirect_uri)

    def setUp(self):
        # Register a user and login.
        # NOTE: merely "creating" a user (i.e. not "registering") does NOT hash the password which is problemating when comparing submitted (and hashed) passwords.
        register_user(**self.userdata)
        self.client.post('/test_login', data={'id': 1})

    def create_client(self, allowed_grant_types='authorization_code'):
        r = self.client.get('/client')
        oauth_client_credentials = self.json(r)

        oauth_client_ = Client.query.get(oauth_client_credentials['client_id'])
        oauth_client_._allowed_grant_types=allowed_grant_types
        self.db.session.commit()

        return oauth_client_credentials['client_id'], oauth_client_credentials['client_secret']

    def get_auth_code(self, client_id, grant_type='authorization_code', scope='userinfo'):
        auth_url = '/oauth/authorize?client_id={0}&response_type=code&grant_type={1}&scope={2}&redirect_uri={3}'.format(client_id, grant_type, scope, self.encoded_redirect_uri)

        # Meant for the more traditional `authorization_code` flow.
        r = self.client.get(auth_url)

        location = r.headers.get('Location')

        # Except this to return the authorization form.
        if location is None and r.status_code == 200:
            return r.data

        # Extract and return the auth code.
        return location.replace('{0}?code='.format(self.default_redirect_uri), '')

    def get_tokens(self, authorization_code, client_id, client_secret=None):
        token_url = '/oauth/token?code={0}&grant_type=authorization_code&client_id={1}&redirect_uri={2}'.format(authorization_code, client_id, self.encoded_redirect_uri)
        if client_secret is None:
            r = self.client.get(token_url)
        else:
            r = self.client.get('{0}&client_secret={1}'.format(token_url, client_secret))
        if r.status_code == 400:
            return None
        return self.json(r)

    def test_client_creation(self):
        # Create the client and gets its id and secret.
        self.assertEqual(Client.query.count(), 0)
        r = self.client.get('/client')
        oauth_client_credentials = self.json(r)
        self.assertGreater(len(oauth_client_credentials['client_id']), 0)
        self.assertGreater(len(oauth_client_credentials['client_secret']), 0)
        self.assertEqual(Client.query.count(), 1)

class OAuthPasswordGrantTypeTest(OAuthTest):
    def test_with_confidential_client(self):
        client_id, client_secret = self.create_client(allowed_grant_types='password')
        client = Client.query.get(client_id)
        client.is_confidential = True
        self.db.session.commit()

        self.assertEqual(Token.query.count(), 0)
        #self.assertEqual(Grant.query.count(), 0)

        r = self.client.post('/oauth/token', data={
            'client_id': client_id,
            'client_secret': client_secret,
            'grant_type': 'password',
            'username': self.userdata['email'],
            'password': self.userdata['password']
        })
        data = self.json(r)

        self.assertTrue('access_token' in data)
        self.assertTrue('refresh_token' in data)
        self.assertEqual(data['token_type'], 'Bearer')
        self.assertEqual(data['scope'], 'userinfo')
        self.assertEqual(Token.query.count(), 1)
        #self.assertEqual(Grant.query.count(), 1)

    def test_not_in_allowed_grant_types(self):
        # Only allow `authorization_code`
        client_id, client_secret = self.create_client(allowed_grant_types='authorization_code')
        client = Client.query.get(client_id)
        client.is_confidential = True
        self.db.session.commit()

        r = self.client.post('/oauth/token', data={
            'client_id': client_id,
            'client_secret': client_secret,
            'grant_type': 'password',
            'username': self.userdata['email'],
            'password': self.userdata['password']
        })
        data = self.json(r)

        self.assertEqual(r.status_code, 400)
        self.assertEqual(data['error'], 'unauthorized_client')

    def test_with_confidential_client_invalid_password(self):
        client_id, client_secret = self.create_client(allowed_grant_types='password')
        client = Client.query.get(client_id)
        client.is_confidential = True
        self.db.session.commit()

        r = self.client.post('/oauth/token', data={
            'client_id': client_id,
            'client_secret': client_secret,
            'grant_type': 'password',
            'username': self.userdata['email'],
            'password': 'wrong_password'
        })
        data = self.json(r)

        self.assertEqual(data['error'], 'invalid_grant')

    def test_with_confidential_client_invalid_email(self):
        client_id, client_secret = self.create_client(allowed_grant_types='password')
        client = Client.query.get(client_id)
        client.is_confidential = True
        self.db.session.commit()

        r = self.client.post('/oauth/token', data={
            'client_id': client_id,
            'client_secret': client_secret,
            'grant_type': 'password',
            'username': 'wrong_email@email.com',
            'password': self.userdata['password']
        })
        data = self.json(r)

        self.assertEqual(data['error'], 'invalid_grant')

    def test_with_public_client(self):
        client_id, client_secret = self.create_client(allowed_grant_types='password')
        r = self.client.post('/oauth/token', data={
            'client_id': client_id,
            'client_secret': client_secret,
            'grant_type': 'password',
            'username': self.userdata['email'],
            'password': self.userdata['password']
        })
        data = self.json(r)
        self.assertEqual(data['error'], 'invalid_client')

    def test_with_confidential_client_invalid_scope(self):
        client_id, client_secret = self.create_client(allowed_grant_types='password')
        client = Client.query.get(client_id)
        client.is_confidential = True
        self.db.session.commit()

        r = self.client.post('/oauth/token', data={
            'client_id': client_id,
            'client_secret': client_secret,
            'grant_type': 'password',
            'scope': 'invalid',
            'username': self.userdata['email'],
            'password': self.userdata['password']
        })
        data = self.json(r)

        self.assertEqual(r.status_code, 400)
        self.assertEqual(data['message'], 'Invalid scope.')


class OAuthAuthCodeGrantTypeTest(OAuthTest):
    def test_when_user_confirms(self):
        client_id, client_secret = self.create_client(allowed_grant_types='authorization_code')

        scope = 'userinfo'
        auth_form = self.get_auth_code(
                client_id,
                grant_type='authorization_code',
                scope=scope
        )

        self.assertNotEqual(auth_form, None)

        # Authorize the client...
        r = self.client.post('/oauth/authorize', data={
            'confirm': 'yes',
            'client_id': client_id,
            'scope': scope,
            'response_type': 'code',
            'grant_type': 'authorization_code',
            'redirect_uri': self.default_redirect_uri
        })

        code = r.headers['Location'].replace('{0}?code='.format(self.default_redirect_uri), '')

        tokens = self.get_tokens(code, client_id)

        self.assertGreater(len(tokens['access_token']), 0)
        self.assertGreater(len(tokens['refresh_token']), 0)
        self.assertEqual(tokens['token_type'], 'Bearer')
        self.assertEqual(tokens['scope'], 'userinfo')

        self.assertEqual(Token.query.count(), 1)
        self.assertEqual(Grant.query.count(), 1)

    def test_when_user_doesnt_confirm(self):
        client_id, client_secret = self.create_client(allowed_grant_types='authorization_code')

        scope = 'userinfo'
        auth_form = self.get_auth_code(
                client_id,
                grant_type='authorization_code',
                scope=scope
        )

        self.assertNotEqual(auth_form, None)

        # Authorize the client...
        r = self.client.post('/oauth/authorize', data={
            'confirm': 'no',
            'client_id': client_id,
            'scope': scope,
            'response_type': 'code',
            'grant_type': 'authorization_code',
            'redirect_uri': self.default_redirect_uri
        })

        self.assertEqual(r.headers['Location'],'{0}?error=access_denied'.format(self.default_redirect_uri))
