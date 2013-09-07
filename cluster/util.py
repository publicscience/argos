"""
Some utility functions.
"""

import os, subprocess, time
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


# Eventually Fabric can replace this.
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
    subprocess.call(ssh + cmd)

# Eventually Fabric can replace this.
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

    # Get output of command to check for errors.
    results = _call_process(scp)

    # Check if we couldn't connect, and try again.
    tries = 0
    while b'Connection refused' in results[1] and tries < 20:
        time.sleep(2)
        results = _call_process(scp)

# Eventually Fabric can replace this.
def _call_process(cmd):
    """
    Convenience method for calling a process and getting its results.

    Args:
        | cmd (list)    -- list of args for the command.
    """
    return subprocess.Popen(cmd, stderr=subprocess.PIPE).communicate()

