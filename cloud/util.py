"""
Some utility functions.
"""

import os
from string import Template

def load_script(filename, **kwargs):
    """
    Loads a script from this directory as bytes.
    This script will be passed as `user-data`.

    Args:
        | filename (str)    -- the filename or path of the script to open.
        | **kwargs          -- optional keyword arguments of a variable and
                            the value to replace it with in the script.

    When you specify `**kwargs`, say `foo=bar`, then every instance of `$foo`
    will be replaced with `bar`.
    """
    script = open(get_filepath(filename), 'r').read()

    # Substitute for specified vars.
    if kwargs:
        script = Template(script).substitute(**kwargs)

    # Turn into bytes.
    return script.encode('utf-8')


def get_filepath(filename):
    """
    Gets filepath for a file
    relative to this directory.
    """
    dir = os.path.dirname(__file__)
    return os.path.abspath(os.path.join(dir, filename))
