"""
Patches
=========
Various patches for expediting
evaluation processes.
"""

from unittest.mock import patch

def patch_external():
    """
    Patch out methods which need to interface with
    external services which aren't necessary for evaluation.
    """
    patches = [
            patch('argos.util.storage.save_from_url', autospec=True, return_value='fakeimage.jpg')
    ]
    for p in patches:
        p.start()
    return patches

def start_patches():
    patches = [
            patch('argos.core.brain.summarize.summarize', autospec=True, return_value=['foo']),
            patch('argos.core.brain.summarize.multisummarize', autospec=True, return_value=['foo'])
    ]
    for p in patches:
        p.start()
    return patches

def stop_patches(patches):
    for p in patches:
        p.stop()
