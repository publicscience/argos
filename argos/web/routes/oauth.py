from argos.web.app import app
from argos.web.models.oauth import Grant, Client, Token, InvalidScope, InvalidGrantType
from argos.datastore import db

from flask import jsonify, request, render_template, abort, redirect, url_for
from flask_oauthlib.provider import OAuth2Provider
from flask_security.core import current_user
from flask.ext.security import login_required, LoginForm
from flask_security.utils import login_user
from werkzeug.security import gen_salt

from datetime import datetime, timedelta

oauth = OAuth2Provider(app)
GRANT_LIFETIME = 3600

@app.errorhandler(InvalidScope)
def handle_invalid_scope(error):
    response = jsonify({'message': error.message})
    response.status_code = error.status_code
    return response

@app.errorhandler(InvalidGrantType)
def handle_invalid_grant_type(error):
    response = jsonify({'message': error.message})
    response.status_code = error.status_code
    return response

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
    for token in tokens:
        db.session.delete(token)

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

@app.route('/oauth/token')
@oauth.token_handler
def access_token():
    return None

@app.route('/oauth/authorize', methods=['GET', 'POST'])
@login_required
@oauth.authorize_handler
def authorize(*args, **kwargs):
    """
    Authorization endpoint for OAuth2.
    Successful interaction with this endpoint yields an access token
    for the requesting client.

    Please note that I am not very confident of this current approach's
    security; it involves a shaky workaround to implement the resource owner
    password credentials (ROPC) OAuth2 flow for the official mobile app.

    Mobile applications are considered "public" clients because their client
    credentials (client id and client secret) cannot reliably be kept secure,
    since if they are bundled with the application they are potentially accessible
    to anyone who has the app on their phone.

    But the ROPC flow works like this:

        * User opens the mobile app and is greated with a native login view.
        * User enters their credentials and hits "Login".
        * POST to `/oauth/authorize?client_id=<CLIENT_ID>&response_type=code&grant_type=resource_owner_credentials&scope=userinfo&redirect_uri=<your redirect uri>`, with data: `{"email": <user email>, "password": <user password>}`
        * Server finds client with the specified client id, checks that the client is allowed the ROPC grant type, and if so, authenticates the user with the provided credentials.
        * If successful, the server responds with the header `Location: <your redirect uri>/?code=<your authorization code>`
        * In the mobile app, you can extract the authorization code and exchange it for the access token by sending a GET request to `/oauth/token?code=<your authorization code>&grant_type=authorization_code&client_id=<your client_id>&redirect_uri=<your redirect uri>`
        * If successful, the server responds with something like: `{"refresh_token": "Z9QAolFevdLXjO7OR1ImJ1pkqc248j", "scope": "userinfo", "access_token": "wvjTny7CXEVEQSfyxC1MSP11NEPnlj", "token_type": "Bearer"}`

    Clearly this is not the ideal flow and not really according to OAuth2 specifications. Anyone can discover and use the client id to imitate the official client since there is no (and cannot be any) verification of client authenticity with a client secret. Unless the provider server is secured with SSL/HTTPS, passwords are sent out in the open. It is only a temporary solution.

    A potential long-term solution is to use OAuth2's "client credentials" flow and consider each *installation* of the mobile application as a *separate* client. Thus each installation has its own unique client id and client secret, relevant only for that particular user. This still may not be very good (haven't thought it all the way through).

    For some more info see:

        * https://stackoverflow.com/questions/14574846/client-authentication-on-public-client
        * https://stackoverflow.com/questions/6190381/how-to-keep-the-client-credentials-confidential-while-using-oauth2s-resource-o
    """

    # NB: request.values refers to values from both
    # the response body and the url parameters.
    client_id = request.values.get('client_id')
    client = Client.query.get(client_id)
    grant_type = request.values.get('grant_type')

    # Check to see if the requested scope(s) are permitted
    # for this client.
    # Since this is a workaround (see below), this looks a bit weird.
    # But if the expected kwargs isn't processed (flask_oauthlib only processes them
    # if it is a GET request), collect the scope information another way.
    #        GET                    POST
    scopes = kwargs.get('scopes') or request.values.get('scope').split()
    client.validate_scopes(scopes)

    # Check to see if the requested grant type is permitted
    # for this client.
    client.validate_grant_type(grant_type)

    if request.method == 'GET':
        kwargs['client'] = client
        if grant_type == 'authorization_code':
            # The user must authenticate herself,
            # if not already authenticated.
            if not current_user.is_authenticated():
                return redirect(url_for('security.login', next=url_for('authorize')))

            kwargs['user'] = current_user

            return render_template('authorize.html', **kwargs)

        response = jsonify({'message': 'Invalid grant type for this request. Perhaps you mean a grant_type of `authorization_code`?'})
        response.status_code = 400
        return response

    elif request.method == 'POST':

        # Authenticate on behalf of the user.
        # ONLY TRUSTED CLIENTS should be allowed this grant type.
        # i.e. only official clients, all others should be using
        # grant type of `authorization_code`.
        # This is enforced since clients are by default restrited to only
        # the `authorization_code` grant type, unless explicitly set otherwise.
        # Note: this is a workaround since flask_oauthlib does not support the "password"
        # grant type at the moment (which is equivalent to "resource_owner_credentials").
        if grant_type == 'resource_owner_credentials':
            form = LoginForm(request.form, csrf_enabled=False)
            if form.validate_on_submit():
                login_user(form.user)
                return True
            else:
                print(form.errors)
                return False

        # Otherwise, assume this request is coming from
        # the authorization_code's authorize form.
        else:
            confirm = request.form.get('confirm', 'no')
            return confirm == 'yes'


@app.route('/client')
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
