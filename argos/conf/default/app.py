from os import environ as env

DEBUG = True
SQLALCHEMY_DATABASE_URI = "postgresql://argos_user:password@localhost:5432/argos_dev"
KNOWLEDGE_HOST = 'localhost'
DATASETS_PATH = '~/env/argos.core/data/knowledge/'
JENA_PATH = '~/env/argos.core/jena/jena'

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

AWS_ACCESS_KEY_ID = env.get('ARGOS_AWS_ACCESS_KEY_ID')
AWS_SECRET_ACCESS_KEY = env.get('ARGOS_AWS_SECRET_ACCESS_KEY')
S3_BUCKET_NAME = 'argos_development_storage'

# Error emails
EMAIL_HOST = 'smtp.gmail.com'
EMAIL_PORT = 587
EMAIL_HOST_USER = 'argos.errors@gmail.com'
EMAIL_HOST_PASSWORD = 'your-pass'
ADMINS = ['ftzeng@gmail.com']
