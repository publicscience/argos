"""
Article similarity patches
==========================
Any methods you define here which include
'similarity' in their name will be
used as alternative similarity methods
for evaluating article similarity.
"""

from unittest.mock import patch
from argos.core.models import Article

def simple_similarity(self, article):
    return 1.0
