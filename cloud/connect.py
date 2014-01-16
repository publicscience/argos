"""
Connect
==============

Connect to cloud services.
"""

from boto.ec2.autoscale import AutoScaleConnection
from boto.ec2 import connect_to_region
from boto.ec2.cloudwatch import connect_to_region as cw_connect_to_region

# Load configuration.
from cloud import config
c = config.load('cloud')

REGION = c['REGION']
ACCESS_KEY = c['AWS_ACCESS_KEY']
SECRET_KEY = c['AWS_SECRET_KEY']


def asg():
    """
    Create an AutoScale Group connection.
    """
    return AutoScaleConnection(ACCESS_KEY, SECRET_KEY)


def ec2():
    """
    Creates an EC2 connection.
    """
    return connect_to_region(
                REGION,
                aws_access_key_id=ACCESS_KEY,
                aws_secret_access_key=SECRET_KEY
           )


def clw():
    """
    Creates a CloudWatch connection.
    """
    return cw_connect_to_region(
                    REGION,
                    aws_access_key_id=ACCESS_KEY,
                    aws_secret_access_key=SECRET_KEY
                 )

