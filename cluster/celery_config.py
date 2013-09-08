# Used to try getting env variables first.
import os

# Celery config.
# Broker (message queue) url.
BROKER_URL = os.getenv('BROKER_URL', 'amqp://guest@localhost//')

# Result backend.
CELERY_RESULT_BACKEND = 'mongodb'
CELERY_MONGODB_BACKEND_SETTINGS = {
    'host': os.getenv('DB_HOST', 'localhost'),
    'port': 27017,
    'database': 'celery',

    # What collection to store task metadata.
    'taskmeta_collection': 'taskmeta'
}

# What modules to import on start.
CELERY_IMPORTS = ('cluster','digester.wikidigester',)

# Propagate chord errors when they come up.
CELERY_CHORD_PROPAGATES = True

CELERYD_LOG_FILE="logger/logs/celery.log"
