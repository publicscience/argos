from argos.datastore import db

from argos.web.models.user import User, Auth, AuthExistsForUserException

from flask import Blueprint, session, request, url_for, jsonify, g
from flask_oauthlib.client import OAuth
from flask_security.utils import logout_user, login_user

oauth = OAuth()

bp = Blueprint('social', __name__, url_prefix='/social')

twitter = oauth.remote_app('twitter', app_key='TWITTER')
facebook = oauth.remote_app('facebook', app_key='FACEBOOK')
google = oauth.remote_app('google', app_key='GOOGLE')

@bp.route('/twitter')
def twitter_authorize():
    return twitter.authorize(callback=url_for('twitter_authorized', _external=True))

@bp.route('/facebook')
def facebook_authorize():
    return facebook.authorize(callback=url_for('facebook_authorized', _external=True))

@bp.route('/google')
def google_authorize():
    return google.authorize(callback=url_for('google_authorized', _external=True))

@bp.route('/logout')
def logout():
    for token in ['twitter', 'facebook', 'google']:
        session.pop('{0}_oauth'.format(token), None)
    logout_user()

@twitter.tokengetter
def get_twitter_token():
    return session.get('twitter_oauth')

@facebook.tokengetter
def get_facebook_token():
    return session.get('facebook_oauth')

@google.tokengetter
def get_google_token():
    return session.get('google_oauth')

@bp.route('/twitter/callback')
@twitter.authorized_handler
def twitter_authorized(resp):
    if resp is None:
        return jsonify(status=401, message='Access denied - did you deny the request?')
    else:
        session['twitter_oauth'] = resp['oauth_token'], resp['oauth_token_secret']
        me = twitter.get('account/verify_credentials.json').data
        userdata = {
                'name': me['name'],
                'email': None, # twitter doesn't allow access to a user's email.
                'image': me['profile_image_url_https']
        }
        _process_user('twitter', me['id_str'], resp['oauth_token'], None, userdata)

@bp.route('/facebook/callback')
@facebook.authorized_handler
def facebook_authorized(resp):
    if resp is None:
        return jsonify(status=401, message='Access denied: {0} (error: {1})'.format(request.args['error_reason'], request.args['error_description']))
    else:
        session['facebook_oauth'] = (resp['access_token'], '')
        me = facebook.get('/me')
        userdata = {
            'name': me['name'],
            'email': me['email'],
            'image': 'https://graph.facebook.com/{0}/picture'.format(id),
        }
        _process_user('facebook', me['id'], resp['access_token'], None, userdata)

@bp.route('/google/callback')
@google.authorized_handler
def google_authorized(resp):
    if resp is None:
        return jsonify(status=401, message='Access denied: {0} (error: {1})'.format(request.args['error_reason'], request.args['error_description']))
    else:
        session['google_oauth'] = (resp['access_token'], '')
        me = google.get('userinfo')
        userdata = {
                'name': me['name'],
                'email': me['email'],
                'image': me['picture']
        }
        _process_user('google', me['id'], resp['access_token'], None, userdata)


def _process_user(provider, provider_id, token, secret, userdata):
    """
    Processes a user to either login or
    add a new authentication to an existing user.
    """
    # If there is already an authenticated user,
    # add this provider to that user.
    if current_user.is_authenticated:
        try:
            current_user.add_provider(provider, provider_id, token, secret, update=True)

        # Conflict - this added authentication already exists but is
        # associated with another user.
        except AuthExistsForUserException as e:
            return jsonify(status=409, message=e.message)

    # Otherwise...
    else:
        # Try to find an existing auth and user.
        auth = Auth.for_provider(provider, provider_id)

        # If one is found, update the auth.
        if auth:
            user = auth.user
            auth.update_token(token, secret)

        # Otherwise create a new user and auth.
        else:
            user = User(**userdata)
            auth = Auth(provider, provider_id, token, secret)
            auth.user = user
            db.session.add(user)
            db.session.add(auth)
        db.session.commit()
        login_user(user)
