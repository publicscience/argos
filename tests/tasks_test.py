import unittest
from adipose import Adipose
from tests import RequiresDB

import math, time
from celery import chord
from cluster.tasks import celery, workers

class TasksTest(unittest.TestCase, RequiresDB):
    @classmethod
    def setUpClass(cls):
        cls.setup_db()

        # Try to run RabbitMQ and a Celery worker.
        # Pipe all output to /dev/null.
        if not workers():
            cls.mq = cls._run_process(['rabbitmq-server'])
            cls.worker = cls._run_process(['celery', 'worker', '--config=cluster.celery_config'])
            # Wait for everything...(need to implement a better checker here)
            time.sleep(5)

    @classmethod
    def tearDownClass(cls):
        cls.teardown_db()

        # Kill RabbitMQ and Celery.
        if cls.worker:
            cls.worker.kill()
        if cls.mq:
            cls.mq.kill()

    def test_chord(self):
        result = chord(pow.s(x, 2) for x in range(100))(combine.s())
        expected = sum([math.pow(x, 2) for x in range(100)])
        self.assertEquals(result.get(), expected)


@celery.task
def pow(x, y):
    return math.pow(x, y)

@celery.task
def combine(nums):
    return sum(nums)
