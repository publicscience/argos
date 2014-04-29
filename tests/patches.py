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
        c_patcher = patch_concepts()
        s_patcher = patch_summarization()
        v_patcher = patch_vectorize()
        a_patcher = patch_aws()
        return_value = f(*args, **kwargs)
        k_patcher.stop()
        c_patcher.stop()
        s_patcher.stop()
        v_patcher.stop()
        a_patcher.stop()
        return return_value
    return decorated

def patch_knowledge():
    # Patch these methods so
    # tests don't require the Fuseki server
    # or a network connection to Wikipedia.
    patcher = Patcher([
        'argos.core.knowledge.knowledge_for',
        'argos.core.knowledge.uri_for_name',
        'argos.core.knowledge.commonness_for_name',
        'argos.core.knowledge.commonness_for_uri'
    ])
    return patcher

def patch_concepts():
    # Patch these methods so
    # tests don't require the Stanford NER server.
    patcher = Patcher([
        'argos.core.brain.concepts'
    ])
    return patcher

def patch_summarization():
    patcher = Patcher([
        'argos.core.brain.summarize.summarize',
        'argos.core.brain.summarize.multisummarize'
    ])
    return patcher

def patch_vectorize():
    patcher = Patcher([
        'argos.core.brain.vectorize'
    ])
    return patcher

def patch_aws():
    patcher = Patcher([
        'argos.util.storage.save_from_url'
    ])
    return patcher

class Patcher():
    """
    This class provides a central place for managing
    commonly used patches for tests.

    Example::

        p = Patcher([
            'argos.core.knowledge.knowledge_for',
            'argos.core.knowledge.uri_for_name'
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

def faux_commonness_for_name(name):
    return 100

def faux_commonness_for_uri(name):
    return 100

def faux_concepts(docs):
    return ['Nautilus', 'Picard']

def faux_summarize(title, text):
    return ['this', 'is', 'a', 'fake', 'summary']

def faux_multisummarize(docs):
    return ['this', 'is', 'a', 'fake', 'summary']

from argos.core.brain import vectorize
cached_vector = vectorize('foo bar')
def faux_vectorize(docs):
    return cached_vector

def faux_save_from_url(url, filename):
    return 'https://s3.amazon.com/fakeimage.jpg'
