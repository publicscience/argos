from argos.web.models.oauth import Grant, Client, Token, InvalidScope, InvalidGrantType
from argos.web.models.user import User
from argos.datastore import db

from flask import Blueprint, jsonify, request, render_template, abort, redirect, url_for
from flask_oauthlib.provider import OAuth2Provider
from flask.ext.security import login_required, login_user, current_user, LoginForm
from werkzeug.security import gen_salt
from werkzeug import MultiDict

from datetime import datetime, timedelta

oauth = OAuth2Provider()

bp = Blueprint('oauth', __name__, url_prefix='/oauth')

GRANT_LIFETIME = 3600

@bp.app_errorhandler(InvalidScope)
def handle_invalid_scope(error):
    response = jsonify({'message': error.message})
    response.status_code = error.status_code
    return response

@bp.app_errorhandler(InvalidGrantType)
def handle_invalid_grant_type(error):
    response = jsonify({'message': error.message})
    response.status_code = error.status_code
    return response

@bp.route('/token', methods=['GET', 'POST'])
@oauth.token_handler
def access_token():
    return None

@bp.route('/authorize', methods=['GET', 'POST'])
@login_required
@oauth.authorize_handler
def authorize(*args, **kwargs):
    """
    Authorization endpoint for OAuth2.
    Successful interaction with this endpoint yields an access token
    for the requesting client.

    Mobile applications are considered "public" clients because their client
    credentials (client id and client secret) cannot reliably be kept secure,
    since if they are bundled with the application they are potentially accessible
    to anyone who has the app on their phone.
    """

    if request.method == 'GET':
        # NB: request.values refers to values from both
        # the response body and the url parameters.
        client_id = kwargs.get('client_id')
        client = Client.query.get(client_id)
        grant_type = request.values.get('grant_type')

        # Check to see if the requested scope(s) are permitted
        # for this client.
        client.validate_scopes(kwargs.get('scopes'))

        # Check to see if the requested grant type is permitted
        # for this client.
        client.validate_grant_type(grant_type)
        kwargs['client'] = client

        # The user must authenticate herself,
        # if not already authenticated.
        if not current_user.is_authenticated():
            return redirect(url_for('security.login', next=url_for('authorize')))

        kwargs['user'] = current_user
        return render_template('authorize.html', **kwargs)

    confirm = request.form.get('confirm', 'no')
    return confirm == 'yes'

@bp.route('/client')
@login_required
def client():
    if not current_user.is_authenticated():
        return redirect('/')
    client = Client(
        client_id=gen_salt(40),
        client_secret=gen_salt(50),
        _redirect_uris='http://localhost:5000/authorized',
        _default_scopes='userinfo',
        _allowed_grant_types='authorization_code refresh_token',
        user_id=current_user.id,
    )
    db.session.add(client)
    db.session.commit()
    return jsonify(
        client_id=client.client_id,
        client_secret=client.client_secret,
    )

@oauth.clientgetter
def load_client(client_id):
    return Client.query.filter_by(client_id=client_id).first()

@oauth.grantgetter
def load_grant(client_id, code):
    return Grant.query.filter_by(client_id=client_id, code=code).first()

@oauth.grantsetter
def save_grant(client_id, code, request, *args, **kwargs):
    expires = datetime.utcnow() + timedelta(seconds=GRANT_LIFETIME)
    grant = Grant(
        client_id=client_id,
        code=code['code'],
        redirect_uri=request.redirect_uri,
        _scopes=' '.join(request.scopes),
        user=current_user,
        expires=expires
    )
    db.session.add(grant)
    db.session.commit()
    return grant

@oauth.tokengetter
def load_token(access_token=None, refresh_token=None):
    if access_token:
        return Token.query.filter_by(access_token=access_token).first()
    elif refresh_token:
        return Token.query.filter_by(access_token=refresh_token).first()

@oauth.tokensetter
def save_token(token, request, *args, **kwargs):
    # Ensure that each client has only one token connected to a user.
    tokens = Token.query.filter_by(
        client_id=request.client.client_id,
        user_id=request.user.id
    )
    for t in tokens:
        db.session.delete(t)

    expires_in = token.pop('expires_in')
    expires = datetime.utcnow() + timedelta(seconds=expires_in)

    token = Token(
        access_token=token['access_token'],
        refresh_token=token['refresh_token'],
        token_type=token['token_type'],
        _scopes=token['scope'],
        expires=expires,
        client_id=request.client.client_id,
        user_id=request.user.id
    )
    db.session.add(token)
    db.session.commit()
    return token

@oauth.usergetter
def get_user(username, password, *args, **kwargs):
    # This is only necessary for the `password` grant type.
    form = LoginForm(MultiDict({'email': username, 'password': password}), csrf_enabled=False)
    if form.validate_on_submit():
        return User.query.filter_by(email=username).first()
    return None
