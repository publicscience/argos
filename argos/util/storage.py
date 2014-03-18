"""
Storage
==============

Coordinator for interacting with storage infrastructure,
i.e. Amazon Web Services S3.
"""

from argos.conf import APP

from boto.s3.connection import S3Connection
from boto.s3.key import Key

from urllib import request
from io import BytesIO

def save_from_url(url, filename):
    """
    Saves a remote file to S3 and returns
    its S3 URL.
    """
    conn = S3Connection(APP['AWS_ACCESS_KEY_ID'], APP['AWS_SECRET_ACCESS_KEY'])
    bucket = conn.get_bucket(APP['S3_BUCKET_NAME'])
    key = Key(bucket)
    key.key = filename
    data = BytesIO(request.urlopen(url).read())
    key.set_contents_from_file(data)
    return key.generate_url(expires_in=None, query_auth=False)
