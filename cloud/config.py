"""
Config
==============

Handles loading configurations.
"""

from configparser import ConfigParser
from cloud.util import get_filepath

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


def cloud_names():
    """
    Loads the names for the cloud's components.
    """

    name = config['cloud']['CLOUD_NAME']

    names = {
            'LC': '{0}-launchconfig'.format(name),
            'AG': '{0}-autoscale'.format(name),
            'SG': '{0}-security'.format(name),
            'DB': '{0}-database'.format(name),
            'MQ': '{0}-broker'.format(name),
            'MASTER': '{0}-master'.format(name),
            'WORKER_IMAGE': '{0}-worker-image'.format(name)
    }
    return names


def update():
    """
    Updates the config file by writing
    any changed values.
    """
    config.write(open(config_file, 'w'))

