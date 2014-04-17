from os import environ as env

# App config
SECRET_KEY = 'development'
AES_KEY = '123456789abcdefg123456789abcdefg' # must be 32 bytes
AES_IV = '123456789abcdefg' # must be 16 bytes
DEBUG = True
ASSETS_DEBUG = True
SQLALCHEMY_DATABASE_URI = "postgresql://argos_user:password@localhost:5432/argos_dev"

KNOWLEDGE_HOST = 'localhost'
DATASETS_PATH = '~/env/argos/data/knowledge/'

# http://bizvizz.com/api/request
BIZVIZZ_API_KEY = 'some key'

# https://www.opensecrets.org/api/admin/index.php?function=signup
OPENSECRETS_API_KEY = 'some key'

AWS_ACCESS_KEY_ID = env.get('ARGOS_AWS_ACCESS_KEY_ID')
AWS_SECRET_ACCESS_KEY = env.get('ARGOS_AWS_SECRET_ACCESS_KEY')
S3_BUCKET_NAME = 'argos_development_storage'

# Error emails
EMAIL_HOST = 'smtp.gmail.com'
EMAIL_PORT = 587
EMAIL_HOST_USER = 'argos.errors@gmail.com'
EMAIL_HOST_PASSWORD = 'your-pass'
ADMINS = ['ftzeng@gmail.com']

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


"""
Base settings for Flask-Security

Included are all settings provided in the Configuration documentation.
Most of them are set to default.
"""

# ==============
# Required
# ==============

SECRET_KEY = 'this-is-our-secret'

# ==============
# Core
# ==============

SECURITY_BLUEPRINT_NAME = 'security'

SECURITY_URL_PREFIX = None

SECURITY_FLASH_MESSAGES = True

SECURITY_PASSWORD_HASH = 'sha512_crypt'
SECURITY_PASSWORD_SALT = 'salty'

SECURITY_EMAIL_SENDER = 'argos.bot@gmail.com'

SECURITY_TOKEN_AUTHENTICATION_KEY = 'auth_token'
SECURITY_TOKEN_AUTHENTICATION_HEADER = 'Authentication-Token'
SECURITY_DEFAULT_HTTP_AUTH_REALM = 'Login Required'

# ==============
# URLs and Views
# ==============

SECURITY_LOGIN_URL = '/login'
SECURITY_LOGOUT_URL = '/logout'
SECURITY_REGISTER_URL = '/register'
SECURITY_RESET_URL = '/reset'
SECURITY_CHANGE_URL = '/change'
SECURITY_CONFIRM_URL = '/confirm'

SECURITY_POST_LOGIN_VIEW = '/'
SECURITY_POST_LOGOUT_VIEW = '/'

SECURITY_CONFIRM_ERROR_VIEW = None

# Note: If the following SECURITY_POST_**_VIEW are None,
#       they default to SECURITY_POST_LOGIN_VIEW
SECURITY_POST_REGISTER_VIEW = None
SECURITY_POST_CONFIRM_VIEW = None
SECURITY_POST_CHANGE_VIEW = None

# Note: If the following is None, defaults to HTTP 403 
#       response
SECURITY_UNAUTHORIZED_VIEW = 'security.login'

# ==============
# Template Paths
# ==============

SECURITY_FORGOT_PASSWORD_TEMPLATE = 'security/forgot_password.jade'
SECURITY_LOGIN_USER_TEMPLATE = 'security/login_user.jade'
SECURITY_REGISTER_USER_TEMPLATE = 'security/register_user.jade'
SECURITY_RESET_PASSWORD_TEMPLATE = 'security/reset_password.jade'
SECURITY_CHANGE_PASSWORD_TEMPLATE = 'security/change_password.html'
SECURITY_SEND_CONFIRMATION_TEMPLATE = 'security/send_confirmation.html'
SECURITY_SEND_LOGIN_TEMPLATE = 'security/send_login.html'

# ==============
# Feature Flags
# ==============

# Note: Flag to create an endpoint for confirming email addresses upon 
#       new account creation (SECURITY_CONFIRM_URL)
SECURITY_CONFIRMABLE = False

# Note: Flag to create a user registration endpoint (SECURITY_REGISTER_URL)
SECURITY_REGISTERABLE = True

# Note: Endpoint of recovery url is SECURITY_RESET_URL
SECURITY_RECOVERABLE = True

# Note: Models should have required fields/attributes to be trackable
SECURITY_TRACKABLE = False

# DO NOT SET TO TRUE
SECURITY_PASSWORDLESS = False

# Note: Endpoint for the change url is SECURITY_CHANGE_URL
SECURITY_CHANGEABLE = True

# ==============
# Email
# ==============

SECURITY_EMAIL_SUBJECT_REGISTER = 'Welcome'

SECURITY_EMAIL_SUBJECT_PASSWORDLESS = 'Login instructions'

SECURITY_EMAIL_SUBJECT_PASSWORD_NOTICE = 'Your password has been reset'

SECURITY_EMAIL_SUBJECT_PASSWORD_CHANGE_NOTICE = 'Your password has been changed'

SECURITY_EMAIL_SUBJECT_CONFIRM = 'Please confirm your email'

# ==============
# Miscellaneous
# ==============

SECURITY_SEND_REGISTER_EMAIL = False
SECURITY_SEND_PASSWORD_CHANGE_EMAIL = False
SECURITY_SEND_PASSWORD_RESET_NOTICE_EMAIL = False

# Note: Always pluralize the time unit
SECURITY_CONFIRM_EMAIL_WITHIN = '5 days'

SECURITY_RESET_PASSWORD_WITHIN = '5 days'

SECURITY_LOGIN_WITHIN = '1 days'

SECURITY_LOGIN_WITHOUT_CONFIRMATION = False

SECURITY_CONFIRM_SALT = 'confirm-salt'
SECURITY_RESET_SALT = 'reset-salt'
SECURITY_LOGIN_SALT = 'login-salt'
SECURITY_REMEMBER_SALT = 'remember-salt'
SECURITY_DEFAULT_REMEMBER_ME = True
