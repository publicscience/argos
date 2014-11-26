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

SECURITY_FORGOT_PASSWORD_TEMPLATE = 'security/forgot_password.html'
SECURITY_LOGIN_USER_TEMPLATE = 'security/login_user.jade'
SECURITY_REGISTER_USER_TEMPLATE = 'security/register_user.html'
SECURITY_RESET_PASSWORD_TEMPLATE = 'security/reset_password.html'
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
