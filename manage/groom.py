"""
Groom
=====

Various management commands which
are for fixes and touch ups and so on.

These aren't really meant to be permanent;
i.e. you should solve the underlying issues
rather than rely on these commands. But they
are temporary fixes.
"""

from argos.conf import APP

from flask.ext.script import Command, Option

from boto.s3.connection import S3Connection
from boto.s3.key import Key
import os

class FixSVGCommand(Command):
    """
    Fixes the Content-Type
    (and permissions)
    for SVG files on S3.

    Fix for:
    argos.util.storage setting of Content-Type
    for SVG files doesn't seem to persist to AWS?
    https://github.com/publicscience/argos/issues/115
    """

    def run(self):
        conn = S3Connection(APP['AWS_ACCESS_KEY_ID'], APP['AWS_SECRET_ACCESS_KEY'])
        bucket = conn.get_bucket(APP['S3_BUCKET_NAME'])

        for key in bucket.list():
            if os.path.splitext(key.name)[-1] == '.svg':
                print('found key {0}'.format(key.name))
                key = bucket.get_key(key.name)
                if key.content_type != 'image/svg+xml':
                    print('setting content-type...')
                    new_key = key.copy(key.bucket, key.name, metadata={'Content-Type': 'image/svg+xml'})
                    new_key.make_public()
                print('existing content type: {0}'.format(key.content_type))
                key.make_public()
