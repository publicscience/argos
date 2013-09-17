"""
Manage
==============

Manage various aspects of a cluster.
"""

import time

from boto.ec2.blockdevicemapping import BlockDeviceMapping, BlockDeviceType
from boto.exception import EC2ResponseError
from cluster import connect

import logging
logger = logging.getLogger(__name__)

def security_group(name, desc='A security group.', ports=[80]):
    """
    Creates or gets an existing security group,
    and authorizes the specified ports.

    Args:
        | name (str)    -- the name of the security group.
        | desc (str)    -- the description of the security group.
        | ports (list)  -- list of the ports to open on the security group.
    """
    ec2 = connect.ec2()
    sec_group = get_security_group(name)
    if not sec_group:
        sec_group = ec2.create_security_group(name, desc)

    # Authorize specified ports.
    for port in ports:
        sec_group.authorize('tcp', port, port, '0.0.0.0/0')

    # Authorize internal communication.
    sec_group.authorize(src_group=sec_group)

    return sec_group


def get_security_group(name):
    """
    Get a security group by name.

    Args:
        | name (str)    -- the name of the security group.
    """
    ec2 = connect.ec2()
    for sg in ec2.get_all_security_groups():
        if sg.name == name:
            return sg


def delete_security_group(name, purge=False):
    """
    Delete a security group by name.

    Args:
        | name (str)    -- name of the security group
        | purge (bool)  -- whether or not to terminate all instances
                           in order to delete the group.
    """
    ec2 = connect.ec2()
    try:
        ec2.delete_security_group(name=name)
    except EC2ResponseError as e:
        # Check if there are still instances in the group.
        sg = get_security_group(name)
        if sg:
            sg_instances = sg.instances()

            # Purge instances.
            if purge:
                logger.info('Security group still has instances. Terminating instances and trying again...')
                for instance in sg_instances:
                    instance.terminate()
                wait_until_terminated(sg_instances)

                # Try deleting again...
                delete_security_group(name)
            else:
                logger.error('Could not delete security group. It still has running instances.')

        else:
            logger.warning('Could not delete security group. It may already be deleted.')


def create_block_device(size=10, delete=False):
    """
    Create a BlockDeviceMapping and a BlockDevice.

    Args:
        | size (int)        -- size in GB for the volume
        | delete (bool)     -- whether or not to delete the volume
                               when its instance has terminated.
    """
    block_device = BlockDeviceType(size=size, delete_on_termination=delete)
    bdm = BlockDeviceMapping()
    bdm['/dev/sda1'] = block_device
    return bdm


def wait_until_ready(instance):
    """
    Wait until an instance is ready.
    """
    istatus = instance.update()
    while istatus == 'pending':
        time.sleep(10)
        istatus = instance.update()


def wait_until_terminated(instance):
    """
    Wait until an instance or instances is terminated.
    """
    if isinstance(instance, list):
        instances = instance
        while len(instances) > 0:
            time.sleep(10)
            instances = [i for i in instances if i.update() != 'terminated']
    else:
        istatus = instance.update()
        while istatus == 'shutting-down':
            time.sleep(10)
            istatus = instance.update()

