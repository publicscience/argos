from datetime import datetime

from argos.datastore import db, Model

from flask.ext.security import Security, UserMixin, RoleMixin

# Table connecting users and roles
roles_users = db.Table('roles_users',
        db.Column('user_id', db.Integer(), db.ForeignKey('user.id')),
        db.Column('role_id', db.Integer(), db.ForeignKey('role.id')))

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
    id              = db.Column(db.BigInteger(), primary_key=True)
    provider        = db.Column(db.String(255))
    provider_id     = db.Column(db.String(255))
    access_token    = db.Column(db.String(255))
    user_id         = db.Column(db.Integer, db.ForeignKey('user.id'))

    def __init__(self, provider_id, provider, access_token):
        self.provider_id = provider_id
        self.provider = provider
        self.access_token = access_token

        # Generate a unique id for this auth based on the provider and the provider id.
        self.id = Auth.make_id(provider, provider_id)

    @staticmethod
    def find_by_provider(provider_id, provider):
        id = Auth.make_id(provider, provider_id)
        return Auth.query.get(id)

    @staticmethod
    def make_id(provider_id, provider):
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

    def __init__(self, **kwargs):
        for key in kwargs:
            setattr(self, key, kwargs[key])

    @staticmethod
    def create_or_update(provider_id, provider, access_token, **userdata):
        # Try to find existing auth.
        id = Auth.make_id(provider, provider_id)
        auth = Auth.query.get(id)

        if auth:
            # If an existing auth is found, update
            # the access token and get & update the associated user.
            auth.access_token = access_token
            user = auth.user
            for key in userdata:
                setattr(user, key, userdata[key])

            # TO DO: add conflict resolution
            # i.e. compare the retrieved auth's user
            # with the current user (if there is one)
            # if they are different, prompt merging of the two
            # accounts.

        else:
            # Otherwise, create a new auth and a new user for it.
            auth = Auth(provider_id, provider, access_token)
            user = User(**userdata)
            auth.user = user
            db.session.add(auth)
            db.session.add(user)

        db.session.commit()
        return user
