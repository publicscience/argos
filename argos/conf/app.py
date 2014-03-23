from os import environ as env

# App config
SECRET_KEY = 'development'
AES_KEY = '123456789abcdefg123456789abcdefg' # must be 32 bytes
AES_IV = '123456789abcdefg' # must be 16 bytes
DEBUG = True
SQLALCHEMY_DATABASE_URI = "postgresql://argos_user:password@localhost:5432/argos_dev"

AWS_ACCESS_KEY_ID = env.get('ARGOS_AWS_ACCESS_KEY_ID')
AWS_SECRET_ACCESS_KEY = env.get('ARGOS_AWS_SECRET_ACCESS_KEY')
S3_BUCKET_NAME = 'argos_development_storage'

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

# Security Config
SECURITY_SEND_REGISTER_EMAIL = False
SECURITY_SEND_PASSWORD_CHANGE_EMAIL = False
SECURITY_SEND_PASSWORD_RESET_NOTICE_EMAIL = False
