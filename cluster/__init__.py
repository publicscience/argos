"""
Cluster
==============

Setup and manage an autoscaling cluster.

Here, an EC2 AutoScale Group is used.

The following are created:
    * AMI of the worker machine
    * Master EC2 instance
    * Security Group
    * Launch Configuration
    * AutoScaling Group
    * Scaling Policies
    * CloudWatch MetricAlarms

And they can all also be dismantled.

Configuration is in `aws_config.ini`.
"""

from boto.ec2.blockdevicemapping import BlockDeviceMapping, BlockDeviceType
from boto.ec2.autoscale import AutoScaleConnection, LaunchConfiguration, AutoScalingGroup, ScalingPolicy
from boto.ec2.cloudwatch import MetricAlarm
from boto.ec2.cloudwatch import connect_to_region as cw_connect_to_region
from boto.ec2 import connect_to_region
from boto.exception import EC2ResponseError

import os, time, subprocess, base64
from cluster.util import get_filepath, load_script, ssh, scp

# Logging
from logger import logger
logger = logger(__name__)

# Boto logging.
import logging
logging.basicConfig(filename='logger/logs/boto.log', level=logging.DEBUG)

# Load configuration.
from configparser import ConfigParser
config = ConfigParser()

# See if the config file is available,
# if not, try the sample file.
CONFIG_FILE = get_filepath('aws_config.ini')
try:
    with open(CONFIG_FILE): pass
except IOError:
    CONFIG_FILE = get_filepath('aws_config-sample.ini')
config.read(CONFIG_FILE)
c = config['CONFIG']

REGION = c['REGION']
NAME = c['CLUSTER_NAME']
INSTANCE_USER = c['INSTANCE_USER']
ACCESS_KEY = c['AWS_ACCESS_KEY']
SECRET_KEY = c['AWS_SECRET_KEY']
KEYPAIR_NAME = c['KEYPAIR_NAME']
PATH_TO_KEY = get_filepath(c['PATH_TO_KEY'])
PATH_TO_DEPLOY_KEYS = c['PATH_TO_DEPLOY_KEYS']
BASE_AMI_ID = c['BASE_AMI_ID']

LC_NAME = '%s-launchconfig' % NAME
AG_NAME = '%s-autoscale' % NAME
SG_NAME = '%s-security' % NAME
MASTER_NAME = '%s-master' % NAME
WORKER_IMAGE_NAME = '%s-worker-image' % NAME

# By default, worker AMI is same as base AMI.
WORKER_AMI_ID = c.get('WORKER_AMI_ID', BASE_AMI_ID)

def commission():
    """
    Setup a new cluster.
    """

    logger.info('Commissioning new cluster...')

    # Check to see if the AutoScale Group already exists.
    if group_exists():
        logger.info('The AutoScale Group already exists, exiting!')
        return

    conn_asg = _connect_asg()
    conn_ec2 = _connect_ec2()

    # Get availability zones for region.
    zones = [zone.name for zone in conn_ec2.get_all_zones()]

    logger.info('Creating the worker/base images...')
    WORKER_AMI_ID = create_worker_image()

    # Create a new security group.
    # Authorize HTTP, MongoDB, and RabbitMQ ports.
    logger.info('Creating the security group (%s)...' % SG_NAME)
    sec_group = _security_group(SG_NAME, 'The cluster security group.', ports=[80, 27017, 5672])

    # Create an EBS (block storage) for the image.
    # Size is in GB.
    # Need a lot of space for the Wiki dump on MongoDB.
    # Do NOT delete this volume on termination, since it will have our processed data.
    bdm = _block_device(size=120, delete=False)

    # Create the Salt Master/RabbitMQ/MongoDB server.
    # The Master instance is a souped-up worker, so we use the worker image.
    logger.info('Creating the master instance (%s)...' % MASTER_NAME)
    logger.info('Using AMI %s' % WORKER_AMI_ID)
    master_init_script = load_script('setup_master.sh')
    reservations = conn_ec2.run_instances(
                       WORKER_AMI_ID,
                       key_name=KEYPAIR_NAME,
                       security_groups=[SG_NAME],
                       instance_type='m1.small',
                       user_data=master_init_script,
                       block_device_map=bdm
                   )
    instance = reservations.instances[0]

    # Wait until the instance is ready.
    logger.info('Waiting for master instance to launch...')
    _wait_until_ready(instance)
    logger.info('Master instance has launched at %s. Configuring...' % instance.public_dns_name)

    # Update config.
    c['MASTER_PUBLIC_DNS'] = instance.public_dns_name
    config.write(open(CONFIG_FILE, 'w'))

    # Tag the instance with a name so we can find it later.
    instance.add_tag('name', MASTER_NAME)

    # NOTE: Fabric does not yet support Py3.3.
    # Set the host for Fabric to connect to.
    #env.hosts = [instance.public_dns_name]
    #env.user = INSTANCE_USER
    #env.key_filename = PATH_TO_KEY

    # For now, using subprocess Popen and call.
    # Not sure if this is really the best solution...
    env = {
            'host': instance.public_dns_name,
            'user': INSTANCE_USER,
            'key_filename': PATH_TO_KEY
    }

    # Replace the $salt_master var in the raw Minion init script with the Master DNS name,
    # so Minions will know where to connect to.
    minion_init_script = load_script('setup_minion.sh', master_dns=instance.private_dns_name)

    # Create the launch configuration.
    logger.info('Creating the launch configuration (%s)...' % LC_NAME)
    launch_config = LaunchConfiguration(
                        name=LC_NAME,
                        image_id=WORKER_AMI_ID,         # AMI ID for autoscaling instances.
                        key_name=KEYPAIR_NAME,          # The name of the EC2 keypair.
                        user_data=minion_init_script,   # User data: the initialization script for the instances.
                        security_groups=[SG_NAME],      # Security groups the instance will be in.
                        instance_type='m1.small',       # Instance size.
                        instance_monitoring=True        # Enable monitoring (for CloudWatch).
                    )

    # Create the launch configuration on AWS.
    conn_asg.create_launch_configuration(launch_config)

    # Create the autoscaling group.
    logger.info('Creating the autoscaling group (%s)...' % AG_NAME)
    autoscaling_group = AutoScalingGroup(
                            group_name=AG_NAME,
                            availability_zones=zones,
                            launch_config=launch_config,
                            min_size=1,  # minimum group size
                            max_size=4,  # maximum group size
                            connection=conn_asg
                        )

    # Create the autoscaling group on AWS.
    conn_asg.create_auto_scaling_group(autoscaling_group)

    # Create the scaling policies.
    # These scaling policies change the size of the group.
    logger.info('Creating scaling policies...')
    scale_up_policy = ScalingPolicy(
                          name='scale-up',
                          adjustment_type='ChangeInCapacity',
                          as_name=AG_NAME,
                          scaling_adjustment=1,
                          cooldown=180
                      )
    scale_dn_policy = ScalingPolicy(
                          name='scale-down',
                          adjustment_type='ChangeInCapacity',
                          as_name=AG_NAME,
                          scaling_adjustment=-1,
                          cooldown=180
                      )

    # Create the scaling policies on AWS.
    conn_asg.create_scaling_policy(scale_up_policy)
    conn_asg.create_scaling_policy(scale_dn_policy)

    # Some extra parameters are created on the policies
    # after they are created on AWS. We need to re-fetch them
    # to edit them.
    scale_up_policy = conn_asg.get_all_policies(
                          as_group=AG_NAME,
                          policy_names=['scale-up']
                      )[0]
    scale_dn_policy = conn_asg.get_all_policies(
                          as_group=AG_NAME,
                          policy_names=['scale-down']
                      )[0]

    # Create CloudWatch alarms.
    logger.info('Creating CloudWatch MetricAlarms...')
    cloudwatch = _connect_clw()

    # We need to specify the "dimensions" of this alarm,
    # which describes what it watches (here, the whole autoscaling group).
    alarm_dimensions = {'AutoScalingGroupName': AG_NAME}

    # Create the scale up alarm.
    # Scale up when average CPU utilization becomes greater than 70%.
    scale_up_alarm = MetricAlarm(
                        name='scale-up-on-cpu',
                        namespace='AWS/EC2',
                        metric='CPUUtilization',
                        statistic='Average',
                        comparison='>',
                        threshold='70',
                        period='60',
                        evaluation_periods=2,
                        alarm_actions=[scale_up_policy.policy_arn],
                        dimensions=alarm_dimensions
                     )
    cloudwatch.create_alarm(scale_up_alarm)

    # Create the scale down alarm.
    # Scale down when average CPU utilization becomes less than 40%.
    scale_dn_alarm = MetricAlarm(
                        name='scale-down-on-cpu',
                        namespace='AWS/EC2',
                        metric='CPUUtilization',
                        statistic='Average',
                        comparison='<',
                        threshold='40',
                        period='60',
                        evaluation_periods=2,
                        alarm_actions=[scale_dn_policy.policy_arn],
                        dimensions=alarm_dimensions
                     )
    cloudwatch.create_alarm(scale_dn_alarm)

    logger.info('Commissioning complete.')


def decommission():
    """
    Dismantle the cluster.
    """

    logger.info('Decommissioning the cluster...')

    conn_asg = _connect_asg()
    conn_ec2 = _connect_ec2()

    # Delete alarms.
    logger.info('Deleting CloudWatch MetricAlarms...')
    cloudwatch = _connect_clw()
    cloudwatch.delete_alarms(['scale-up-on-cpu', 'scale-down-on-cpu'])

    # Shutdown and delete autoscaling groups.
    # This also deletes the groups' scaling policies.
    logger.info('Deleting the autoscaling group (%s)...' % AG_NAME)
    groups = conn_asg.get_all_groups(names=[AG_NAME])
    for group in groups:
        group_instance_ids = [i.instance_id for i in group.instances]

        # Shutdown all group instances.
        logger.info('Terminating group instances...')
        group.shutdown_instances()

        # If there are still instances left in the group,
        # wait until they shut down.
        if group_instance_ids:
            group_instances = [r.instances[0] for r in conn_ec2.get_all_instances(instance_ids=group_instance_ids)]

            logger.info('Waiting for group instances to shutdown...')
            _wait_until_terminated(group_instances)

        # Wait until all group activities have stopped.
        group_activities = group.get_activities()
        while len(group_activities) > 0:
            time.sleep(10)
            group_activities = [a for a in group.get_activities() if a.status_code == 'InProgress']

        # Delete the group.
        group.delete()

    # Delete launch configs.
    logger.info('Deleting the launch configuration (%s)...' % LC_NAME)
    launch_configs = conn_asg.get_all_launch_configurations(names=[LC_NAME])
    for lc in launch_configs:
        lc.delete()

    # Delete the master instance(s).
    logger.info('Deleting the master instance (%s)...' % MASTER_NAME)
    master_instances = conn_ec2.get_all_instances(filters={'tag-key': 'name', 'tag-value': MASTER_NAME})
    for reservation in master_instances:
        for i in reservation.instances:
            i.terminate()
        _wait_until_terminated(reservation.instances)

    # Delete the security group.
    logger.info('Deleting the security group (%s)...' % SG_NAME)
    _delete_security_group(SG_NAME)

    # Delete the worker image.
    delete_worker_image()

    logger.info('Decommissioning complete.')


def create_worker_image():
    """
    Create an AMI for workers,
    based off of the base AMI.
    """

    conn_ec2 = _connect_ec2()
    sg_name = WORKER_IMAGE_NAME

    if _get_security_group(sg_name):
        logger.info('Conflicting security group exists. Deleting...')
        _delete_security_group(sg_name, purge=True)

    # Create a new security group.
    logger.info('Creating a temporary security group...')
    sec_group = conn_ec2.create_security_group(sg_name, 'Temporary, for worker image')

    # Authorize SSH access (temporarily).
    logger.info('Temporarily enabling SSH access to base instance...')
    sec_group.authorize('tcp', 22, 22, '0.0.0.0/0')

    # Create an EBS (block storage) for the image.
    # Size is in GB.
    bdm = _block_device(size=10, delete=True)

    # Create the instance the AMI will be generated from.
    # *Not* using a user data init script here; instead
    # executing it via ssh.
    # Executing the init script via user data makes it
    # difficult to know when the system is ready to be
    # turned into an image.
    # Running the init script manually means image creation
    # can be execute serially after the script is done.
    logger.info('Creating the base instance...')
    reservations = conn_ec2.run_instances(
                       BASE_AMI_ID,
                       key_name=KEYPAIR_NAME,
                       security_groups=[sg_name],
                       instance_type='m1.small',
                       block_device_map=bdm
                   )
    instance = reservations.instances[0]

    # Wait until the instance is ready.
    logger.info('Waiting for base instance to launch...')
    _wait_until_ready(instance)
    logger.info('Base instance has launched at %s. Configuring...' % instance.public_dns_name)

    # Tag the instance with a name so we can find it later.
    instance.add_tag('name', WORKER_IMAGE_NAME)

    env = {
        'host': instance.public_dns_name,
        'user': INSTANCE_USER,
        'key_filename': PATH_TO_KEY
    }

    # Setup base instance with the Salt state tree.
    # This waits until the instance is ready to accept commands.
    _transfer_salt(env['host'], env['user'], env['key_filename'])

    # Transfer init script.
    logger.info('Transferring the init script...')
    image_init_script = get_filepath('setup_image.sh')
    scp(image_init_script, '/tmp/', host=env['host'], user=env['user'], key=env['key_filename'])

    # Execute the script.
    logger.info('Executing the init script...')
    ssh(['sudo', 'bash', '/tmp/setup_image.sh'], host=env['host'], user=env['user'], key=env['key_filename'])

    # Delete the script.
    logger.info('Cleaning up the init script...')
    ssh(['sudo', 'rm', '/tmp/setup_image.sh'], host=env['host'], user=env['user'], key=env['key_filename'])

    # Create the AMI and get its ID.
    logger.info('Creating worker image...')
    WORKER_AMI_ID = instance.create_image(WORKER_IMAGE_NAME, description='Base image for workers')

    # Update config.
    c['WORKER_AMI_ID'] = WORKER_AMI_ID
    config.write(open(CONFIG_FILE, 'w'))

    # Wait until worker is ready.
    worker_image = conn_ec2.get_all_images([WORKER_AMI_ID])[0]
    _wait_until_ready(worker_image)
    logger.info('Created worker image with id %s' % WORKER_AMI_ID)

    # Clean up the worker image infrastructure.
    clean_worker_image()

    logger.info('AMI creation complete. (%s)' % WORKER_AMI_ID)

    return WORKER_AMI_ID

def clean_worker_image():
    """
    Decommissions the infrastructure used to
    construct the worker image.
    """
    logger.info('Cleaning up worker image infrastructure...')
    conn_ec2 = _connect_ec2()

    # Terminate base instance.
    logger.info('Terminating base instance...')
    base_instances = conn_ec2.get_all_instances(filters={'tag-key': 'name', 'tag-value': WORKER_IMAGE_NAME})
    for reservation in base_instances:
        for i in reservation.instances:
            i.terminate()
        _wait_until_terminated(reservation.instances)

    # Delete security group.
    logger.info('Deleting the temporary security group...')
    _delete_security_group(WORKER_IMAGE_NAME, purge=True)

    logger.info('Worker image cleanup complete.')


def delete_worker_image(image_id=WORKER_AMI_ID):
    """
    Deregisters the worker AMI and deletes its snapshot.
    """
    conn_ec2 = _connect_ec2()
    if image_id:
        logger.info('Deleting worker image with id %s' % image_id)
        try:
            try:
                conn_ec2.deregister_image(image_id, delete_snapshot=True)

            # If the snapshot doesn't exist, just try deregistering the image.
            except AttributeError as e:
                conn_ec2.deregister_image(image_id)

        except EC2ResponseError as e:
            logger.error('Could not deregister the image. It may already be deregistered.')


def group_exists():
    """
    Checks if the AutoScale Group exists.

    Returns:
        | int   -- number of AutoScale Groups found.
    """
    conn_asg = _connect_asg()

    groups = conn_asg.get_all_groups(names=[AG_NAME])
    return len(groups)


def _connect_asg():
    """
    Create an AutoScale Group connection.
    """
    return AutoScaleConnection(ACCESS_KEY, SECRET_KEY)


def _connect_ec2():
    """
    Creates an EC2 connection.
    """
    return connect_to_region(
                REGION,
                aws_access_key_id=ACCESS_KEY,
                aws_secret_access_key=SECRET_KEY
           )


def _connect_clw():
    """
    Creates a CloudWatch connection.
    """
    return cw_connect_to_region(
                    REGION,
                    aws_access_key_id=ACCESS_KEY,
                    aws_secret_access_key=SECRET_KEY
                 )


def _security_group(name, desc='A security group.', ports=[80]):
    """
    Creates or gets an existing security group,
    and authorizes the specified ports.

    Args:
        | name (str)    -- the name of the security group.
        | desc (str)    -- the description of the security group.
        | ports (list)  -- list of the ports to open on the security group.
    """
    conn_ec2 = _connect_ec2()
    sec_group = _get_security_group(name)
    if not sec_group:
        sec_group = conn_ec2.create_security_group(name, desc)

    # Authorize specified ports.
    for port in ports:
        sec_group.authorize('tcp', port, port, '0.0.0.0/0')

    # Authorize internal communication.
    sec_group.authorize(src_group=sec_group)

    return sec_group


def _get_security_group(name):
    """
    Get a security group by name.

    Args:
        | name (str)    -- the name of the security group.
    """
    conn_ec2 = _connect_ec2()
    for sg in conn_ec2.get_all_security_groups():
        if sg.name == name:
            return sg


def _delete_security_group(name, purge=False):
    """
    Delete a security group by name.

    Args:
        | name (str)    -- name of the security group
        | purge (bool)  -- whether or not to terminate all instances
                           in order to delete the group.
    """
    conn_ec2 = _connect_ec2()
    try:
        conn_ec2.delete_security_group(name=name)
    except EC2ResponseError as e:
        # Check if there are still instances in the group.
        sg = _get_security_group(name)
        if sg:
            sg_instances = sg.instances()

            # Purge instances.
            if purge:
                logger.info('Security group still has instances. Terminating instances and trying again...')
                for instance in sg_instances:
                    instance.terminate()
                _wait_until_terminated(sg_instances)

                # Try deleting again...
                _delete_security_group(name)
            else:
                logger.error('Could not delete security group. It still has running instances.')

        else:
            logger.error('Could not delete security group. It may already be deleted.')


def _block_device(size=10, delete=False):
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


def _wait_until_ready(instance):
    """
    Wait until an instance is ready.
    """
    istatus = instance.update()
    while istatus == 'pending':
        time.sleep(10)
        istatus = instance.update()


def _wait_until_terminated(instance):
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


def _transfer_salt(host, user, keyfile):
    """
    Transfer Salt state and other necessary files
    to the specified host.

    Args:
        | host (str)    -- the host to connect to.
        | user (str)    -- the user to connect as.
        | keyfile (str)    -- the path to the key to connect with.
    """

    # Copy over deploy keys into the Salt state tree.
    logger.info('Copying deploy keys to the Salt state tree...')
    salt_path = get_filepath('salt/')
    deploy_keys_path = get_filepath(PATH_TO_DEPLOY_KEYS)
    deploy_keys = ['id_rsa', 'id_rsa.pub']
    for key in deploy_keys:
        subprocess.Popen([
            'cp',
            os.path.join(deploy_keys_path, key),
            os.path.join(salt_path, 'salt/deploy/')
        ])

    # Wait for SSH to become active...
    time.sleep(10)

    # Copy over Salt state tree to the host.
    # First have to move to a temporary directory.
    # '-o StrictHostKeyChecking no' automatically adds
    # the instance to SSH known hosts.
    logger.info('Secure copying Salt state tree to /tmp/salt on the instance...')
    scp(salt_path, '/tmp/salt', host=host, user=user, key=keyfile)

    # Move it to the real directory.
    logger.info('Moving Salt state tree to /srv/salt on the instance...')
    ssh(['sudo', 'mv', '/tmp/salt/*', '/srv'], host=host, user=user, key=keyfile)

    # Clean up the deploy keys.
    logger.info('Cleaning up deploy keys... ')
    for key in deploy_keys:
        subprocess.Popen([
            'rm',
            os.path.join(salt_path, 'salt/deploy/', key)
        ])
