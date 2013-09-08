"""
Tasks
==============

Provides access to
distributed task processing.
"""

from celery import Celery
from cluster import celery_config

from logger import logger
logger = logger(__name__)

celery = Celery()
celery.config_from_object(celery_config)

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

    logger.info('There are %s workers available.' % len(workers))
    return workers


def active():
    """
    Get info about currently executing tasks.
    """
    try:
        active_tasks = celery.control.inspect().active()
        if not active_tasks:
            logger.info('No active tasks.')
            return False
    except IOError as e:
        logger.error('Error connecting to MQ. Check that it is running.')
        return False

    logger.info('There are %s executing tasks.' % len(active_tasks))
    return active_tasks
