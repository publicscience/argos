"""
Command
==============

Interface for commanding the cluster.
"""

import subprocess, time
from cluster.util import get_filepath, load_script
from cluster.manage import get_security_group

import logging
logger = logging.getLogger(__name__)

# Import cluster config
from cluster import config
c = config.load()
names = config.names()

host, user, key = c['MASTER_PUBLIC_DNS'], c['INSTANCE_USER'], get_filepath(c['PATH_TO_KEY'])
py_path = '/var/app/digester/dev-env/bin/python'


def remote(func):
    """
    Decorator for authorizing then revoking
    ssh access to the master.
    """
    def wrapped():
        rule = ['tcp', 22, 22, '0.0.0.0/0']

        sec_group = get_security_group(names['SG'])
        sec_group.authorize(*rule)

        # Wait a little...
        sleep(5)

        func()

        sec_group.revoke(*rule)
    return wrapped


@remote
def wikidigest():
    """
    Command the cluster to begin WikiDigestion.
    """
    ssh(['sudo', py_path, '/var/app/digester/digest.py'],
            host=host, user=user, key=key)

@remote
def systems_check():
    """
    Check that distributed processing is working ok
    on a newly commissioned cluster.
    """
    pass


# Eventually Fabric can replace all the below.
def ssh(cmd, host=None, user=None, key=None):
    """
    Convenience method for SSHing.

    Args:
        | cmd (list)    -- a list of the command parameters.
        | host (str)    -- the ip or hostname to connect to.
        | user (str)    -- the user to connect as.
        | key (str)     -- path to the key for authenticating.
    """
    ssh = [
        'ssh',
        '-t',
        '-i',
        key,
        '%s@%s' % (user, host)
    ]
    return _call_remote_process(ssh + cmd)


def scp(local, remote, host=None, user=None, key=None):
    """
    Convenience method for SCPing.

    Args:
        | local (str)   -- path to local file or directory to copy.
        | remote (str)  -- path to remote file or directory to copy to.
        | host (str)    -- the ip or hostname to connect to.
        | user (str)    -- the user to connect as.
        | key (str)     -- path to the key for authenticating.
    """
    scp = [
            'scp',
            '-r',
            '-o',
            'StrictHostKeyChecking=no',
            '-i',
            key,
            local,
            '%s@%s:%s' % (user, host, remote)
    ]
    return _call_remote_process(scp)


def _call_remote_process(cmd):
    """
    Calls a remote process and retries
    a few times before giving up.
    """
    # Get output of command to check for errors.
    out, err = _call_process(cmd)

    # Check if we couldn't connect, and try again.
    tries = 0
    while b'Connection refused' in err and tries < 20:
        time.sleep(2)
        out, err = _call_process(cmd)
    return out, err



def _call_process(cmd, log=False):
    """
    Convenience method for calling a process and getting its results.

    Args:
        | cmd (list)    -- list of args for the command.
    """
    out, err = subprocess.Popen(cmd, stderr=subprocess.PIPE, stdout=subprocess.PIPE).communicate()
    if out: logger.info(out.decode('utf-8'))
    if err: logger.info(err.decode('utf-8'))
    return out, err

