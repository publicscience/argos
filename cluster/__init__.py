"""
Tasks
==============

Tasks for Celery workers to run.
"""

from celery import Celery
from celery.task.control import inspect
from . import celery_config

from logger import logger

# Expose `manage` when imported.
from . import manage

celery = Celery()
celery.config_from_object(config)

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
        workers = inspect().stats()
        if not workers:
            logger.error('No Celery workers available.')
        return False
    except IOError as e:
        logger.error('Error connecting to MQ. Check that it is running.')
        return False
    return workers
