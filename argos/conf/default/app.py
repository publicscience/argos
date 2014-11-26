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
JENA_PATH = '~/env/argos/jena/jena'

AWS_ACCESS_KEY_ID = env.get('ARGOS_AWS_ACCESS_KEY_ID')
AWS_SECRET_ACCESS_KEY = env.get('ARGOS_AWS_SECRET_ACCESS_KEY')
S3_BUCKET_NAME = 'argos_development_storage'

# Error emails
EMAIL_HOST = 'smtp.gmail.com'
EMAIL_PORT = 587
EMAIL_HOST_USER = 'argos.errors@gmail.com'
EMAIL_HOST_PASSWORD = 'your-pass'
ADMINS = ['ftzeng@gmail.com']

CLUSTERING = {
    'hierarchy_path': '~/env/argos/hierarchy.ihac',
    'lower_limit_scale': 0.7,
    'upper_limit_scale': 1.3,
    'metric': 'euclidean',
    'threshold': 50.0,
    'weights': [1., 90., 30.]
}

from galaxy import conf as galaxy_conf
galaxy_conf.PIPELINE_PATH = '~/env/argos/'
galaxy_conf.STANFORD = {
    'host':  'localhost',
    'port': 8080
}
galaxy_conf.SPOTLIGHT = {
    'host': 'localhost',
    'port': 2222
}
