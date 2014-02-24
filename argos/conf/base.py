"""
Base configuration

These can be overridden in environment-based settings. Many 
of these values are shared among different configuration files.

All variables defined below are used by the application. Some of the 
values are not set until the environment-based configuration file is 
read.
"""

# ===============
# Database config
# ===============

DATABASE = {
    'default': {
        'TYPE': 'postgresql',
        'HOST': 'localhost',
        'USER': 'argos_user',
        'PASSWORD': 'password',
        'PORT': 5432,
        'NAME': 'argos_dev'
    },
    'celery': {
        'TYPE': 'redis',
        'HOST': 'localhost',
        'PORT': 6379,
        'NAME': '0'
    }
}

# Alchemy key
ALCHEMY_KEY = 'alchemy-key'

# ===============
# Email config
# ===============

EMAIL = {
    'default': {
        'HOST': 'smtp.gmail.com',
        'PORT': 587,
        'USER': 'argos.bot@gmail.com',
        'PASS': 'your-pass'
    }
}
