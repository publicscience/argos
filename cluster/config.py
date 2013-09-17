"""
Config
==============

Handles loading configurations.
"""

from configparser import ConfigParser
from cluster.util import get_filepath

config = ConfigParser()
config_file = get_filepath('config.ini')
config.read(config_file)

def load(name):
    """
    Return a section of the config file.

    Args:
        | name (str)    -- the name of the section to return.
    """
    return config[name]


def cluster_names():
    """
    Loads the names for the cluster's components.
    """

    name = config['cluster']['CLUSTER_NAME']

    names = {
            'LC': '%s-launchconfig' % name,
            'AG': '%s-autoscale' % name,
            'SG': '%s-security' % name,
            'DB': '%s-database' % name,
            'MQ': '%s-broker' % name,
            'MASTER': '%s-master' % name,
            'WORKER_IMAGE': '%s-worker-image' % name
    }
    return names


def update():
    """
    Updates the config file by writing
    any changed values.
    """
    config.write(open(config_file, 'w'))

