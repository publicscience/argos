"""
Storage
==============

Coordinator for interacting with storage infrastructure,
i.e. Amazon Web Services S3.
"""

from boto.s3.connection import S3Connection
from boto.s3.key import Key

from urllib import request, error, parse
from io import BytesIO
import os

from argos.conf import APP

from argos.util.logger import logger
logger = logger(__name__)

from argos.util.request import make_request

from http.client import BadStatusLine

def save_from_url(url, filename):
    """
    Saves a remote file to S3 and returns
    its S3 URL.
    """
    try:
        res = make_request(url)

    except error.HTTPError as e:
        # Wikimedia 404 errors are very common, since images may go
        # out of date.
        # So common that for now these exceptions are just ignored.
        if e.code == 404 and 'wikimedia' in url:
            logger.warning('Error requesting {0} : {1}'.format(url, e))

        # Other exceptions are more remarkable and should be brought up.
        else:
            logger.exception('Error requesting {0} : {1}'.format(url, e))
        return None

    except (ConnectionResetError, BadStatusLine, ValueError) as e:
        logger.exception('Error requesting {0} : {1}'.format(url, e))
        return None

    data = BytesIO(res.read())
    return save_from_file(data, filename)

def save_from_file(file, filename):
    """
    Saves file data to S3 and returns
    its S3 URL.
    """
    conn = S3Connection(APP['AWS_ACCESS_KEY_ID'], APP['AWS_SECRET_ACCESS_KEY'])
    bucket = conn.get_bucket(APP['S3_BUCKET_NAME'])
    key = Key(bucket)
    key.key = filename

    # Manually set Content-Type if necessary.
    ext = os.path.splitext(filename)[-1]
    if ext == '.svg':
        key.content_type = 'image/svg+xml'

    key.set_contents_from_file(file)

    # Not sure if this should be called every time.
    key.make_public()

    # Note: this assumes that this key is public.
    return key.generate_url(expires_in=0, query_auth=False)
