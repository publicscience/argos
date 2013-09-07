"""
Command
==============

Interface for commanding the cluster.
"""

# Import cluster config
from cluster import c, _get_security_group, SG_NAME
from cluster.util import get_filepath, load_script, ssh, scp

host, user, key = c['MASTER_PUBLIC_DNS'], c['INSTANCE_USER'], get_filepath(c['PATH_TO_KEY'])


def wikidigest():
    """
    Command the cluster to begin WikiDigestion.
    """
    ssh([])
