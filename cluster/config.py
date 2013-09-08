"""
Config
==============

Handles loading configurations.
"""

from configparser import ConfigParser
from cluster.util import get_filepath

config = ConfigParser()

# See if the config file is available,
# if not, try the sample file.
config_file = get_filepath('aws_config.ini')
try:
    with open(config_file): pass
except IOError:
    config_file = get_filepath('aws_config-sample.ini')
config.read(config_file)


def load():
    """
    Return the AWS configuration.
    """
    return config['CONFIG']


def names():
    """
    Loads the names for the cluster's components.
    """

    name = config['CONFIG']['CLUSTER_NAME']

    names = {
            'LC': '%s-launchconfig' % name,
            'AG': '%s-autoscale' % name,
            'SG': '%s-security' % name,
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

