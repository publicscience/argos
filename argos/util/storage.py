"""
Storage
==============

Coordinator for interacting with storage infrastructure,
i.e. Amazon Web Services S3.
"""

from argos.conf import APP

from boto.s3.connection import S3Connection
from boto.s3.key import Key

from urllib import request, error, parse
from io import BytesIO

def save_from_url(url, filename):
    """
    Saves a remote file to S3 and returns
    its S3 URL.
    """
    try:
        # parse.quote necessary for unicode urls.
        res = request.urlopen(parse.quote(url, safe='/:'))
    except error.HTTPError as e:
        print('Error requesting {0}: {1}'.format(url, e))
        return None
    conn = S3Connection(APP['AWS_ACCESS_KEY_ID'], APP['AWS_SECRET_ACCESS_KEY'])
    bucket = conn.get_bucket(APP['S3_BUCKET_NAME'])
    key = Key(bucket)
    key.key = filename
    data = BytesIO(res.read())
    key.set_contents_from_file(data)

    # Not sure if this should be called every time.
    key.make_public()

    # Note: this assumes that this key is public.
    return key.generate_url(expires_in=0, query_auth=False)