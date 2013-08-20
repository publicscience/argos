"""
Tasks
==============

Tasks for Celery workers to run.
"""

from celery import Celery
from tasks import config

celery = Celery()
celery.config_from_object(config)

@celery.task
def add(x, y):
    return x + y
