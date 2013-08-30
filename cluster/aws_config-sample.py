AWS_ACCESS_KEY = 'your access key'
AWS_SECRET_KEY = 'your secret key'

CLUSTER_NAME = 'cluster'
REGION = 'us-east-1'
AMI_ID= 'my_ami'
KEYPAIR_NAME = 'key_name'
INSTANCE_USER = 'ubuntu'

# Path to your EC2 key.
PATH_TO_KEY = '../keys/ec2key.pem'

# Looks for an `id_rsa.pub` and `id_rsa` in this directory,
# for accessing the Github repository.
PATH_TO_DEPLOY_KEYS = '../keys'

# Use a base Ubuntu 13.04 64bit us-east-1 instance-store image.
# For more, see:
# https://cloud-images.ubuntu.com/locator/ec2/
# Choose according to your region!
BASE_AMI_ID = 'ami-a73371ce'
