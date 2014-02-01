from flask import session, request, url_for, jsonify, g
from flask_oauthlib.client import OAuth
from flask_security.utils import logout_user, login_user
from app import app
from models import User

oauth = OAuth(app)

twitter = oauth.remote_app('twitter', app_key='TWITTER')
facebook = oauth.remote_app('facebook', app_key='FACEBOOK')
google = oauth.remote_app('google', app_key='GOOGLE')

@app.before_request
def before_request():
    # Get the current user before each request.
    g.user = None
    for provider in ['twitter', 'facebook', 'google']:
        oauth = '{0}_oauth'.format(provider)
        if oauth in session:
            g.user = session[oauth]
            break

@app.route('/login')
def login():
    provider = request.args.get('provider')
    if provider == 'twitter':
        return twitter.authorize(callback=url_for('twitter_authorized', _external=True))
    elif provider == 'facebook':
        return facebook.authorize(callback=url_for('facebook_authorized', _external=True))
    elif provider == 'google':
        return google.authorize(callback=url_for('google_authorized', _external=True))
    else:
        return jsonify(status=400, message='The specified provider was not recognized.')

@app.route('/logout')
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

@app.route('/login/auth/twitter')
@twitter.authorized_handler
def twitter_authorized(resp):
    if resp is None:
        return jsonify(status=401, message='Access denied - did you deny the request?')
    else:
        session['twitter_oauth'] = resp
        me = twitter.get('account/verify_credentials.json')
        data = {
                'name': me['name'],
                'email': None, # twitter doesn't allow access to a user's email.
                'image': me['profile_image_url_https']
        }
        user = User.create_or_update(me['id_str'], 'twitter', resp['access_token'], **data)
        login_user(user)

@app.route('/login/auth/facebook')
@facebook.authorized_handler
def facebook_authorized(resp):
    if resp is None:
        return jsonify(status=401, message='Access denied: {0} (error: {1})'.format(request.args['error_reason'], request.args['error_description']))
    else:
        session['facebook_oauth'] = (resp['access_token'], '')
        me = facebook.get('/me')
        data = {
            'name': me['name'],
            'email': me['email'],
            'image': 'https://graph.facebook.com/{0}/picture'.format(id),
        }
        user = User.create_or_update(me['id'], 'facebook', resp['access_token'], **data)
        login_user(user)

@app.route('/login/auth/google')
@google.authorized_handler
def google_authorized(resp):
    if resp is None:
        return jsonify(status=401, message='Access denied: {0} (error: {1})'.format(request.args['error_reason'], request.args['error_description']))
    else:
        session['google_oauth'] = (resp['access_token'], '')
        me = google.get('userinfo')
        data = {
                'name': me['name'],
                'email': me['email'],
                'image': me['picture']
        }
        user = User.create_or_update(me['id'], 'google', resp['access_token'], **data)
        login_user(user)


