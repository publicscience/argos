from os import environ as env

# http://bizvizz.com/api/request
BIZVIZZ_API_KEY = 'some key'

# https://www.opensecrets.org/api/admin/index.php?function=signup
OPENSECRETS_API_KEY = 'some key'

# http://instagram.com/developer/clients/manage/
INSTAGRAM_CLIENT_ID = 'some client id'

# https://www.flickr.com/services/apps/create/
FLICKR_CLIENT_ID = 'some client id'

# http://sunlightfoundation.com/api/
SUNLIGHT_API_KEY = 'some api key'

TWITTER = {
    'consumer_key':         env.get('ARGOS_TWITTER_CONSUMER_KEY'),
    'consumer_secret':      env.get('ARGOS_TWITTER_CONSUMER_SECRET'),
    'base_url':             'https://api.twitter.com/1.1/',
    'request_token_url':    'https://api.twitter.com/oauth/request_token',
    'access_token_url':     'https://api.twitter.com/oauth/access_token',
    'authorize_url':        'https://api.twitter.com/oauth/authenticate',
}
GOOGLE = {
    'consumer_key':         env.get('ARGOS_GOOGLE_CONSUMER_KEY'),
    'consumer_secret':      env.get('ARGOS_GOOGLE_CONSUMER_SECRET'),
    'base_url':             'https://www.googleapis.com/oauth2/v1/',
    'request_token_url':    None,
    'access_token_method':  'POST',
    'access_token_url':     'https://accounts.google.com/o/oauth2/token',
    'authorize_url':        'https://accounts.google.com/o/oauth2/auth',
    'request_token_params': {
        'scope': 'https://www.googleapis.com/auth/userinfo.profile https://www.googleapis.com/auth/userinfo.email',
        'access_type': 'offline'    # to get a refresh token
    }
}
FACEBOOK = {
    'consumer_key':         env.get('ARGOS_FACEBOOK_CONSUMER_KEY'),
    'consumer_secret':      env.get('ARGOS_FACEBOOK_CONSUMER_SECRET'),
    'base_url':             'https://graph.facebook.com/',
    'request_token_url':    None,
    'access_token_url':     '/oauth/access_token',
    'authorize_url':        'https://www.facebook.com/dialog/oauth',
    'request_token_params': {'scope': 'email'}
}


