from datetime import datetime
from Crypto.Cipher import AES

from argos.web.app import app
from argos.datastore import db, Model

from flask.ext.security import Security, UserMixin, RoleMixin

# Table connecting users and roles
roles_users = db.Table('roles_users',
        db.Column('user_id', db.Integer(), db.ForeignKey('user.id')),
        db.Column('role_id', db.Integer(), db.ForeignKey('role.id')))

class AuthExistsForUserException(Exception):
    pass

class Role(Model, RoleMixin):
    """
    A user's Role

    Attributes:

        * id -> Integer (Primary Key)
        * name -> String (Unique)
        * description -> String
    """
    id              = db.Column(db.Integer(), primary_key=True)
    name            = db.Column(db.String(80), unique=True)
    description     = db.Column(db.String(255))


class Auth(Model):
    """
    Represents a third-party authentication.
    """
    id                      = db.Column(db.BigInteger(), primary_key=True)
    provider                = db.Column(db.String(255))
    provider_id             = db.Column(db.String(255))
    access_token            = db.Column(db.String(255))
    _access_token_secret    = db.Column('access_token_secret', db.LargeBinary(255))
    user_id                 = db.Column(db.Integer, db.ForeignKey('user.id'))

    def __init__(self, provider, provider_id,  access_token, access_token_secret=None):
        self.provider_id = provider_id
        self.provider = provider
        self.access_token = access_token
        self.access_token_secret = access_token_secret

        # Generate a unique id for this auth based on the provider and the provider id.
        self.id = Auth.gen_id(provider, provider_id)

    def update_token(self, access_token, access_token_secret=None):
        """
        Updates token for an authentication.

        Enforcing that access tokens and their
        secrets must be updated in tandem.
        May need to revisit this decision later.

        Args:
            | access_token (str)        -- the access token
            | access_token_secret (str) -- the access token secret
        """

        # If the auth has a token and no secret, just update the token.
        if self.access_token and self.access_token_secret is None:
            self.access_token = access_token

        # Otherwise, the auth has a token and a secret,
        # and a new secret must be present.
        elif access_token_secret is None:
            raise Exception('This authentication requires a token secret, which was not specified.')

        else:
            self.access_token = access_token
            self.access_token_secret = access_token_secret

    @property
    def access_token_secret(self):
        if self._access_token_secret is not None:
            dec = AES.new(app.config['AES_KEY'], AES.MODE_CFB, app.config['AES_IV'])
            return dec.decrypt(self._access_token_secret).decode('utf-8')

    @access_token_secret.setter
    def access_token_secret(self, value):
        if value is not None:
            enc = AES.new(app.config['AES_KEY'], AES.MODE_CFB, app.config['AES_IV'])
            self._access_token_secret = enc.encrypt(value)

    @staticmethod
    def for_provider(provider, provider_id):
        """
        Find an Auth instance by provider.

        Args:
            | provider (str)        -- the provider name, e.g. 'twitter'
            | provider_id (str)     -- the user id assigned by the provider
        """
        id = Auth.gen_id(provider, provider_id)
        return Auth.query.get(id)

    @staticmethod
    def gen_id(provider, provider_id):
        """
        Generates a unique id for an Auth.
        """
        return hash(provider + provider_id)


class User(Model, UserMixin):
    """
    A user

    Attributes:

        * id -> Integer (Primary Key)
        * email -> String (Unique)
        * password -> String (Unique)
        * active -> Bool
        * confirmed_at -> DateTime
        * roles -> [Role]
    """
    id              = db.Column(db.Integer(), primary_key=True)
    email           = db.Column(db.String(255), unique=True)
    image           = db.Column(db.String(255), unique=True)
    name            = db.Column(db.String(255), unique=True)
    password        = db.Column(db.String(255))
    active          = db.Column(db.Boolean())
    confirmed_at    = db.Column(db.DateTime())
    auths           = db.relationship('Auth', backref='user', lazy='dynamic')
    roles           = db.relationship('Role', secondary=roles_users,
                            backref=db.backref('users', lazy='dynamic'))
    created_at      = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at      = db.Column(db.DateTime, default=datetime.utcnow)

    def __init__(self, auth=None, **kwargs):
        for key in kwargs:
            setattr(self, key, kwargs[key])

    def add_provider(self, provider, provider_id, access_token, access_token_secret=None, update=True):
        """
        Add a new provider authentication to this user.

        Raises an AuthExistsForUserException if this authentication
        already exists and is associated with another user.

        Args:
            | provider (str)            -- the provider name, e.g. 'twitter'
            | provider_id (str)         -- the id assigned by the provider
            | access_token (str)        -- the access token
            | access_token_secret (str) -- the access token secret
            | update (bool)             -- whether or not to update the existing
                                        provider authentication, if found (default: True)
        """
        # Check to see if this auth already exists.
        auth = Auth.for_provider(provider, provider_id)
        if auth:
            if auth.user is not self:
                raise AuthExistsForUserException('Found an existing authorization for {0} associated with another user.'.format(provider))
            elif update:
                auth.update_token(access_token, access_token_secret)
        else:
            auth = Auth(provider, provider_id, access_token, access_token_secret)
            auth.user = self
            db.session.add(auth)

        db.session.commit()

        return auth

    @staticmethod
    def for_provider(provider, provider_id):
        """
        Find an User instance by provider.

        Args:
            | provider (str)        -- the provider name, e.g. 'twitter'
            | provider_id (str)     -- the user id assigned by the provider
        """
        auth = Auth.for_provider(provider, provider_id)
        if auth:
            return auth.user
        return None
