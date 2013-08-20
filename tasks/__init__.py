"""
Tasks
==============

Tasks for Celery workers to run.
"""

from celery import Celery
from tasks import config
from adipose import Adipose

celery = Celery()
celery.config_from_object(config)

db = Adipose('test', 'celery')
db.empty()

@celery.task
def add(x, y, key):
    db.add({key: x + y})
