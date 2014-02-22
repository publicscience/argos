from argos.web.app import app
from argos.datastore import db, Model

class InvalidScope(Exception):
    def __init__(self, message):
        Exception.__init__(self)
        self.message = message
        self.status_code = 400

class InvalidGrantType(Exception):
    def __init__(self, message):
        Exception.__init__(self)
        self.message = message
        self.status_code = 400

VALID_SCOPES = ['userinfo']

class Client(db.Model):
    client_id      = db.Column(db.String(40), primary_key=True)
    client_secret  = db.Column(db.String(55), unique=True, index=True, nullable=False)

    user_id         = db.Column(db.ForeignKey('user.id'))
    user            = db.relationship('User')

    name            = db.Column(db.String(40))
    desc            = db.Column(db.String(400))

    is_confidential = db.Column(db.Boolean)

    _redirect_uris  = db.Column(db.Text)
    _default_scopes = db.Column(db.Text)

    _allowed_grant_types = db.Column(db.Text)

    def validate_scopes(self, scopes):
        for scope in scopes:
            if scope not in VALID_SCOPES:
                raise InvalidScope('Invalid scope.')
        return True

    def validate_grant_type(self, grant_type):
        if grant_type not in self.allowed_grant_types:
            raise InvalidGrantType('Invalid or missing grant type.')
        return True

    @property
    def client_type(self):
        if self.is_confidential:
            return 'confidential'
        return 'public'

    @property
    def redirect_uris(self):
        if self._redirect_uris:
            return self._redirect_uris.split()
        return []

    @property
    def default_redirect_uri(self):
        return self.redirect_uris[0]

    @property
    def default_scopes(self):
        if self._default_scopes:
            return self._default_scopes.split()
        return []

    @property
    def allowed_grant_types(self):
        if self._allowed_grant_types:
            return self._allowed_grant_types.split()
        return []


class Grant(db.Model):
    id              = db.Column(db.Integer, primary_key=True)

    user_id         = db.Column(db.ForeignKey('user.id', ondelete='CASCADE'))
    user            = db.relationship('User')

    client_id       = db.Column(db.ForeignKey('client.client_id'), nullable=False)
    client          = db.relationship('Client')

    code            = db.Column(db.String(255), index=True, nullable=False)
    redirect_uri    = db.Column(db.String(255))
    expires         = db.Column(db.DateTime)

    _scopes         = db.Column(db.Text)

    def delete(self):
        db.session.delete(self)
        db.session.commit
        return self

    @property
    def scopes(self):
        if self._scopes:
            return self._scopes.split()
        return []


class Token(db.Model):
    id              = db.Column(db.Integer, primary_key=True)

    client_id       = db.Column(db.ForeignKey('client.client_id'), nullable=False)
    client          = db.relationship('Client')

    user_id         = db.Column(db.ForeignKey('user.id'))
    user            = db.relationship('User')

    # Currently OAuthLib only supports bearer tokens.
    token_type      = db.Column(db.String(40))

    access_token    = db.Column(db.String(255), unique=True)
    refresh_token   = db.Column(db.String(255), unique=True)
    expires         = db.Column(db.DateTime)
    _scopes         = db.Column(db.Text)

    @property
    def scopes(self):
        if self._scopes:
            return self._scopes.split()
        return []
