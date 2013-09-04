"""
Cluster
==============

Sets up and manages clusters
for distributed tasks.
"""

from celery import Celery
from cluster import celery_config

from logger import logger
logger = logger(__name__)

# Expose `manage` when imported.
from . import manage

celery = Celery()
celery.config_from_object(celery_config)

import math
from celery import chord
@celery.task
def pow(x, y):
    return math.pow(x, y)

def done(nums):
    return sum(nums)

def test():
    tasks = chord(pow(x, 2) for x in range(100))(done())


def workers():
    """
    Get info about currently available Celery workers.
    If none are available, or there are issues connecting
    to the MQ, returns False.

    Returns:
        | dict      -- dict of available workers.
        OR
        | bool      -- False if no available workers, or cannot connect ot MQ.
    """

    try:
        # Get info on available workers.
        workers = celery.control.inspect().stats()
        if not workers:
            logger.error('No Celery workers available.')
            return False
    except IOError as e:
        logger.error('Error connecting to MQ. Check that it is running.')
        return False
    return workers
