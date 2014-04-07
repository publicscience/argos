import unittest
from tests import RequiresDatabase

import math, time
from celery import chord

from argos.tasks import celery, workers

class TasksTest(RequiresDatabase):
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
