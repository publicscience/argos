"""
Tasks
==============

Tasks for Celery workers to run.
"""

from celery import Celery
from . import celery_config

# Expose `manage` when imported.
from . import manage

celery = Celery()
celery.config_from_object(config)
