from conf.base_security import *

# App config
SECRET_KEY = 'development'
DEBUG = True
SQLALCHEMY_DATABASE_URI = "{DATABASE[default][TYPE]}://{DATABASE[default][HOST]}:{DATABASE[default][PORT]}/{DATABASE[default][NAME]}"

TWITTER = {
    'consumer_key':         'something',
    'consumer_secret':      'something',
    'base_url':             'https://api.twitter.com/1.1/',
    'request_token_url':    'https://api.twitter.com/oauth/request_token',
    'access_token_url':     'https://api.twitter.com/oauth/access_token',
    'authorize_url':        'https://api.twitter.com/oauth/authenticate',
}
GOOGLE = {
    'consumer_key':         'something',
    'consumer_secret':      'something',
    'base_url':             'https://www.googleapis.com/oauth2/v1/',
    'request_token_url':    None,
    'access_token_method':  'POST',
    'access_token_url':     'https://accounts.google.com/o/oauth2/token',
    'authorize_url':        'https://accounts.google.com/o/oauth2/auth',
    'request_token_params': {
        'scope': 'https://www.googleapis.com/auth/userinfo.profile https://www.googleapis.com/auth/userinfo.email'
    }
}
FACEBOOK = {
    'consumer_key':         'something',
    'consumer_secret':      'something',
    'base_url':             'https://graph.facebook.com',
    'request_token_url':    None,
    'access_token_url':     '/oauth/access_token',
    'authorize_url':        'https://www.facebook.com/dialog/oauth',
    'request_token_params': {'scope': 'email'}
}



# Security Config
SECURITY_SEND_REGISTER_EMAIL = False 
SECURITY_SEND_PASSWORD_CHANGE_EMAIL = False 
SECURITY_SEND_PASSWORD_RESET_NOTICE_EMAIL = False 
