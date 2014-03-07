"""
Patches
=======

Provides patches for common external dependencies (e.g. Stanford NER, Apache Fuseki) so they don't need to be running.
"""

from unittest.mock import patch
from functools import wraps

def requires_patches(f):
    @wraps(f)
    def decorated(*args, **kwargs):
        k_patcher = patch_knowledge()
        e_patcher = patch_entities()
        return_value = f(*args, **kwargs)
        k_patcher.stop()
        e_patcher.stop()
        return return_value
    return decorated

def patch_knowledge():
    # Patch these methods so
    # tests don't require the Fuseki server
    # or a network connection to Wikipedia.
    patcher = Patcher([
        'argos.core.brain.knowledge.knowledge_for',
        'argos.core.brain.knowledge.uri_for_name'
    ])
    return patcher

def patch_entities():
    # Patch these methods so
    # tests don't require the Stanford NER server.
    patcher = Patcher([
        'argos.core.brain.entities'
    ])
    return patcher


class Patcher():
    """
    This class provides a central place for managing
    commonly used patches for tests.

    Example::

        p = Patcher([
            'argos.core.brain.knowledge.knowledge_for',
            'argos.core.brain.knowledge.uri_for_name'
        ])

    This will look for the methods `faux_knowledge_for` and
    `faux_uri_for_name` and patch those methods with these fake versions.

    When you're done, simply call::

        p.stop()

    """
    def __init__(self, patch_names):
        self.patchers = []
        for patch_name in patch_names:
            func_name = 'faux_{0}'.format(patch_name.split('.')[-1])
            patcher = patch(patch_name)
            mock_method = patcher.start()
            func = globals().get(func_name) # kinda sketched out by this, but works ok
            if func:
                mock_method.side_effect = func
            else:
                raise Exception('No mock function has been defined for this name.')
            self.patchers.append(patcher)

    def stop(self):
        for patcher in self.patchers:
            patcher.stop()



"""
Faux Functions
==============

The mock functions used in place of
the real ones.
"""

def faux_knowledge_for(name=None, uri=None, fallback=None):
    if uri:
        return {
            'summary': 'this is fake summary for uri {0}'.format(uri),
            'image': 'http://www.argos.la/image.jpg',
            'name': 'Canonical name'
        }
    if name:
        return {
            'summary': 'this is fake summary for name {0}'.format(name),
            'image': 'http://www.argos.la/image.jpg',
            'name': name
        }
    return None

def faux_uri_for_name(name):
    return "http://fauxpedia.org/resource/{0}".format(name)

def faux_entities(docs):
    return ['Nautilus', 'Picard']
