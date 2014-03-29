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

def logger(name):
    # Create the logger.
    logger = logging.getLogger(name)

    # Configure the logger.
    logger.setLevel(logging.INFO)
    formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')

    # Output to file.
    fh = logging.FileHandler(log_path)
    fh.setFormatter(formatter)
    logger.addHandler(fh)

    # Output to console.
    ch = logging.StreamHandler()
    ch.setFormatter(formatter)
    logger.addHandler(ch)

    if not APP['DEBUG']:
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

    return logger
