from unittest.mock import patch
from functools import wraps

def requires_knowledge_patches(f):
    @wraps(f)
    def decorated(*args, **kwargs):
        patcher = patch_knowledge()
        return_value = f(*args, **kwargs)
        patcher.stop()
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

# Patch these methods so
# tests don't require the Fuseki server
# or a network connection to Wikipedia.
def faux_knowledge_for(name=None, uri=None, fallback=None):
    if uri:
        return {
            'summary': 'this is fake summary for uri {0}'.format(uri),
            'image': 'http://www.argos.la/image.jpg'
        }
    if name:
        return {
            'summary': 'this is fake summary for name {0}'.format(name),
            'image': 'http://www.argos.la/image.jpg'
        }
    return None

def faux_uri_for_name(name):
    return "http://fauxpedia.org/resource/{0}".format(name)
