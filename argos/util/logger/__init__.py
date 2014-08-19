"""
Logger
==============

Logger!
"""

import logging
from logging import handlers
from os import path

from argos.conf import APP

log_path = path.join(path.dirname(__file__), 'logs/log.log')

def logger(name, null=False):
    # Create the logger.
    logger = logging.getLogger(name)

    if null:
        nh = logging.NullHandler()
        logger.addHandler(nh)
        return logger

    # Configure the logger.
    logger.setLevel(logging.INFO)
    formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')

    if APP['DEBUG']:
        # Output to file, if DEBUG=True
        fh = logging.FileHandler(log_path)
        fh.setFormatter(formatter)
        logger.addHandler(fh)

        # Output to console.
        ch = logging.StreamHandler()
        ch.setFormatter(formatter)
        logger.addHandler(ch)

    else:
        # Output to email.
        mh = handlers.SMTPHandler(
                (APP['EMAIL_HOST'], APP['EMAIL_PORT']),
                APP['EMAIL_HOST_USER'],
                APP['ADMINS'],
                'Argos Error :(',
                credentials=(
                    APP['EMAIL_HOST_USER'],
                    APP['EMAIL_HOST_PASSWORD']
                ),
                secure=()
        )
        mh.setLevel(logging.ERROR)
        logger.addHandler(mh)

    return logger
