BROKER_URL = 'amqp://guest@localhost//'

# Don't need a result backend.
#CELERY_RESULT_BACKEND = 'mongodb'
#CELERY_MONGODB_BACKEND_SETTINGS = {
    #'host': 'localhost',
    #'port': 27017,
    #'database': 'some_db',

    ## What collection to store task metadata.
    #'taskmeta_collection': 'taskmeta'
#}

# What modules to import on start.
CELERY_IMPORTS = ('tasks','digester.wikidigester',)
