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

from boto.ec2.autoscale import LaunchConfiguration, AutoScalingGroup, ScalingPolicy
from boto.ec2.cloudwatch import MetricAlarm
from boto.exception import EC2ResponseError

import os, time, subprocess, base64
from cluster.util import get_filepath, load_script
from cluster import manage, connect, command, config

# Logging
from logger import logger
logger = logger(__name__)

# Cluster logging.
import logging
logging.basicConfig(filename='logger/logs/cluster.log', level=logging.DEBUG)

c = config.load('cluster')
names = config.cluster_names()

INSTANCE_USER = c['INSTANCE_USER']
KEYPAIR_NAME = c['KEYPAIR_NAME']
PATH_TO_KEY = get_filepath(c['PATH_TO_KEY'])
PATH_TO_DEPLOY_KEYS = c['PATH_TO_DEPLOY_KEYS']
BASE_AMI_ID = c['BASE_AMI_ID']

# By default, worker AMI is same as base AMI.
WORKER_AMI_ID = c.get('WORKER_AMI_ID', BASE_AMI_ID)

def commission(use_existing_image=True, min_size=1, max_size=4, instance_type='m1.medium', master_instance_type='m1.medium', database_instance_type='m1.medium', ssh=False):
    """
    Setup a new cluster.

    Args:
        | use_existing_image (bool)     -- whether or not to try
                                           using an existing image.
        | min_size (int)                -- the minimum size of the cluster
        | max_size (int)                -- the maximum size of the cluster
        | instance_type (str)           -- the type of instance to use in the cluster.
                                           See: https://aws.amazon.com/ec2/instance-types/instance-details/
        | master_instance_type (str)    -- the type of master instance to use for the cluster.
                                           Recommended that it has at least a few GB of memory.
        | database_instance_type (str)  -- the type of database instance to use for the cluster.
        | ssh (bool)                    -- whether or not to enable SSH access on the cluster.
    """

    logger.info('Commissioning new cluster...')

    # Check to see if the AutoScale Group already exists.
    if group_exists():
        logger.info('The AutoScale Group already exists, exiting!')
        return

    asg = connect.asg()
    ec2 = connect.ec2()

    # Try to use an existing image if specified.
    if use_existing_image:
        logger.info('Looking for an existing worker image...')
        images = ec2.get_all_images(filters={'name': names['WORKER_IMAGE']})
        if images:
            WORKER_AMI_ID = images[0].id

            logger.info('Existing worker image found. (%s)' % WORKER_AMI_ID)

            # Update config.
            c['WORKER_AMI_ID'] = WORKER_AMI_ID
            config.update()
        else:
            # Create a new one if necessary.
            logger.info('No existing worker image found. A new one is being created...')
            WORKER_AMI_ID = create_worker_image()

    # Or just create a new one.
    else:
        logger.info('Creating the worker/base images...')
        WORKER_AMI_ID = create_worker_image()

    # Get availability zones for region.
    zones = [zone.name for zone in ec2.get_all_zones()]

    # Create a new security group.
    # Authorize HTTP and MongoDB ports.
    logger.info('Creating the security group (%s)...' % names['SG'])
    ports = [80, 27017]
    if ssh:
        logger.info('SSH is enabled!')
        ports.append(22)
    sec_group = manage.security_group(names['SG'], 'The cluster security group.', ports=ports)

    logger.info('Using AMI %s' % WORKER_AMI_ID)

    # Create the database instance.
    logger.info('Creating the database instance (%s)...' % names['DB'])

    # Create an EBS (block storage) for the image.
    # Size is in GB.
    # Need a lot of space for the Wiki dump on MongoDB.
    # Do NOT delete this volume on termination, since it will have our processed data.
    db_bdm = manage.create_block_device(size=500, delete=False)

    db_init_script = load_script('scripts/setup_db.sh')
    db_reservations = ec2.run_instances(
                       WORKER_AMI_ID,
                       key_name=KEYPAIR_NAME,
                       security_groups=[names['SG']],
                       instance_type=database_instance_type,
                       user_data=db_init_script,
                       block_device_map=db_bdm
                   )
    db_instance = db_reservations.instances[0]

    # Wait until the database instance is ready.
    logger.info('Waiting for database instance to launch...')
    manage.wait_until_ready(db_instance)
    logger.info('Database instance has launched at %s.' % db_instance.public_dns_name)

    # Update config.
    c['DATABASE_PUBLIC_DNS'] = db_instance.public_dns_name
    config.update()

    # Tag the instance with a name so we can find it later.
    db_instance.add_tag('name', names['DB'])

    # Create the Salt Master/RabbitMQ server.
    # The Master instance is a souped-up worker, so we use the worker image.
    logger.info('Creating the master instance (%s)...' % names['MASTER'])

    bdm = manage.create_block_device(size=150, delete=True)
    master_init_script = load_script('scripts/setup_master.sh',
            db_dns=db_instance.private_dns_name
    )
    reservations = ec2.run_instances(
                       WORKER_AMI_ID,
                       key_name=KEYPAIR_NAME,
                       security_groups=[names['SG']],
                       instance_type=master_instance_type,
                       user_data=master_init_script,
                       block_device_map=bdm
                   )
    instance = reservations.instances[0]

    # Wait until the master instance is ready.
    logger.info('Waiting for master instance to launch...')
    manage.wait_until_ready(instance)
    logger.info('Master instance has launched at %s. Configuring...' % instance.public_dns_name)

    # Update config.
    c['MASTER_PUBLIC_DNS'] = instance.public_dns_name
    config.update()

    # Tag the instance with a name so we can find it later.
    instance.add_tag('name', names['MASTER'])

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
    minion_init_script = load_script('scripts/setup_minion.sh',
            master_dns=instance.private_dns_name,
            db_dns=db_instance.private_dns_name
    )

    # Create the launch configuration.
    logger.info('Creating the launch configuration (%s)...' % names['LC'])
    logger.info('Cluster is composed of %s instances.' % instance_type)
    launch_config = LaunchConfiguration(
                        name=names['LC'],
                        image_id=WORKER_AMI_ID,         # AMI ID for autoscaling instances.
                        key_name=KEYPAIR_NAME,          # The name of the EC2 keypair.
                        user_data=minion_init_script,   # User data: the initialization script for the instances.
                        security_groups=[names['SG']],      # Security groups the instance will be in.
                        instance_type=instance_type,       # Instance size.
                        instance_monitoring=True        # Enable monitoring (for CloudWatch).
                    )

    # Create the launch configuration on AWS.
    asg.create_launch_configuration(launch_config)

    # Create the autoscaling group.
    logger.info('Creating autoscaling group (%s)...' % names['AG'])
    autoscaling_group = AutoScalingGroup(
                            group_name=names['AG'],
                            availability_zones=zones,
                            launch_config=launch_config,
                            min_size=min_size,  # minimum group size
                            max_size=max_size,  # maximum group size
                            connection=asg
                        )

    # Create the autoscaling group on AWS.
    asg.create_auto_scaling_group(autoscaling_group)

    # Create the scaling policies.
    # These scaling policies change the size of the group.
    logger.info('Creating scaling policies...')
    scale_up_policy = ScalingPolicy(
                          name='scale-up',
                          adjustment_type='ChangeInCapacity',
                          as_name=names['AG'],
                          scaling_adjustment=1,
                          cooldown=180
                      )
    scale_dn_policy = ScalingPolicy(
                          name='scale-down',
                          adjustment_type='ChangeInCapacity',
                          as_name=names['AG'],
                          scaling_adjustment=-1,
                          cooldown=180
                      )

    # Create the scaling policies on AWS.
    asg.create_scaling_policy(scale_up_policy)
    asg.create_scaling_policy(scale_dn_policy)

    # Some extra parameters are created on the policies
    # after they are created on AWS. We need to re-fetch them
    # to edit them.
    scale_up_policy = asg.get_all_policies(
                          as_group=names['AG'],
                          policy_names=['scale-up']
                      )[0]
    scale_dn_policy = asg.get_all_policies(
                          as_group=names['AG'],
                          policy_names=['scale-down']
                      )[0]

    # Create CloudWatch alarms.
    logger.info('Creating CloudWatch MetricAlarms...')
    cloudwatch = connect.clw()

    # We need to specify the "dimensions" of this alarm,
    # which describes what it watches (here, the whole autoscaling group).
    alarm_dimensions = {'AutoScalingGroupName': names['AG']}

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


def decommission(preserve_image=True):
    """
    Dismantle the cluster.

    Args:
        | preserve_image (bool)     -- whether or not to keep
                                       the worker image.
    """

    logger.info('Decommissioning the cluster...')

    asg = connect.asg()
    ec2 = connect.ec2()

    # Delete alarms.
    logger.info('Deleting CloudWatch MetricAlarms...')
    cloudwatch = connect.clw()
    cloudwatch.delete_alarms(['scale-up-on-cpu', 'scale-down-on-cpu'])

    # Shutdown and delete autoscaling groups.
    # This also deletes the groups' scaling policies.
    logger.info('Deleting the autoscaling group (%s)...' % names['AG'])
    groups = asg.get_all_groups(names=[names['AG']])
    for group in groups:
        group_instance_ids = [i.instance_id for i in group.instances]

        # Shutdown all group instances.
        logger.info('Terminating group instances...')
        group.shutdown_instances()

        # If there are still instances left in the group,
        # wait until they shut down.
        if group_instance_ids:
            group_instances = [r.instances[0] for r in ec2.get_all_instances(instance_ids=group_instance_ids)]

            logger.info('Waiting for group instances to shutdown...')
            manage.wait_until_terminated(group_instances)

        # Wait until all group activities have stopped.
        group_activities = group.get_activities()
        while group_activities:
            time.sleep(10)
            group_activities = [a for a in group.get_activities() if a.status_code == 'InProgress']

        # Delete the group.
        group.delete()

    # Delete launch configs.
    logger.info('Deleting the launch configuration (%s)...' % names['LC'])
    launch_configs = asg.get_all_launch_configurations(names=[names['LC']])
    for lc in launch_configs:
        lc.delete()

    # Delete the master instance(s).
    logger.info('Deleting the master instance (%s)...' % names['MASTER'])
    master_instances = ec2.get_all_instances(filters={'tag-key': 'name', 'tag-value': names['MASTER']})
    for reservation in master_instances:
        for i in reservation.instances:
            i.terminate()
        manage.wait_until_terminated(reservation.instances)

    # Delete the database instance(s).
    logger.info('Deleting the database instance (%s)...' % names['DB'])
    db_instances = ec2.get_all_instances(filters={'tag-key': 'name', 'tag-value': names['DB']})
    for reservation in db_instances:
        for i in reservation.instances:
            i.terminate()
        manage.wait_until_terminated(reservation.instances)

    # Delete the security group.
    logger.info('Deleting the security group (%s)...' % names['SG'])
    manage.delete_security_group(names['SG'])

    # Delete the worker image.
    if not preserve_image:
        delete_worker_image()

    logger.info('Decommissioning complete.')


def create_worker_base():
    """
    Create the base instance for the
    worker image.
    """
    ec2 = connect.ec2()
    sg_name = names['WORKER_IMAGE']

    # Clean up any existing worker base instances,
    # since it will screw things up.
    delete_worker_base()

    try:
        if manage.get_security_group(sg_name):
            logger.info('Conflicting security group exists. Deleting...')
            manage.delete_security_group(sg_name, purge=True)

        # Create a new security group.
        logger.info('Creating a temporary security group...')
        sec_group = ec2.create_security_group(sg_name, 'Temporary, for worker image')

        # Authorize SSH access (temporarily).
        logger.info('Temporarily enabling SSH access to base instance...')
        sec_group.authorize('tcp', 22, 22, '0.0.0.0/0')

        # Create an EBS (block storage) for the image.
        # Size is in GB.
        bdm = manage.create_block_device(size=10, delete=True)

        # Create the instance the AMI will be generated from.
        # *Not* using a user data init script here; instead
        # executing it via ssh.
        # Executing the init script via user data makes it
        # difficult to know when the system is ready to be
        # turned into an image.
        # Running the init script manually means image creation
        # can be executed serially after the script is done.
        logger.info('Creating the base instance...')
        reservations = ec2.run_instances(
                           BASE_AMI_ID,
                           key_name=KEYPAIR_NAME,
                           security_groups=[sg_name],
                           instance_type='m1.medium',
                           block_device_map=bdm
                       )
        instance = reservations.instances[0]

        # Wait until the instance is ready.
        logger.info('Waiting for base instance to launch...')
        manage.wait_until_ready(instance)
        logger.info('Base instance has launched at %s. Configuring...' % instance.public_dns_name)

        # Tag the instance with a name so we can find it later.
        instance.add_tag('name', names['WORKER_IMAGE'])

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
        image_init_script = get_filepath('scripts/setup_image.sh')
        command.scp(image_init_script, '/tmp/', host=env['host'], user=env['user'], key=env['key_filename'])

        # Execute the script.
        logger.info('Executing the init script...')
        command.ssh(['sudo', 'bash', '/tmp/setup_image.sh'], host=env['host'], user=env['user'], key=env['key_filename'])

        # Delete the script.
        logger.info('Cleaning up the init script...')
        command.ssh(['sudo', 'rm', '/tmp/setup_image.sh'], host=env['host'], user=env['user'], key=env['key_filename'])

        logger.info('Worker base instance successfully created.')

        return instance

    except EC2ResponseError as e:
        logger.error('Error creating the worker base instance, undoing...')

        # Try to undo all the changes.
        delete_worker_base()

        # Re-raise the error.
        raise e


def create_worker_image(use_existing_base=True):
    """
    Create an AMI for workers,
    based off of the base instance.
    """
    ec2 = connect.ec2()

    # Clean up any existing worker images.
    # Things usually mess up if there
    # is conflicting/existing stuff.
    delete_worker_image()

    # Try to use an existing base if specified.
    if use_existing_base:
        logger.info('Looking for an existing worker base instance...')
        base_instances = ec2.get_all_instances(filters={'tag-key': 'name', 'tag-value': names['WORKER_IMAGE']})
        for reservation in base_instances:
            if reservation.instances:
                base_instance = reservation.instances[0]
                if base_instance.update() != 'ready':
                    continue
                else:
                    logger.info('Existing worker base instance found.')
                    break
        else:
            # Create a new one if necessary.
            logger.info('No existing worker base instance found. A new one is being created...')
            base_instance = create_worker_base()
    else:
        logger.info('Creating a new worker base instance...')
        base_instance = create_worker_base()

    try:
        # Create the AMI and get its ID.
        logger.info('Creating worker image...')
        WORKER_AMI_ID = base_instance.create_image(names['WORKER_IMAGE'], description='Base image for workers')

        # Update config.
        c['WORKER_AMI_ID'] = WORKER_AMI_ID
        config.update()

        # Wait until worker is ready.
        worker_image = ec2.get_all_images([WORKER_AMI_ID])[0]
        manage.wait_until_ready(worker_image)
        logger.info('Created worker image with id %s' % WORKER_AMI_ID)

        # Clean up the worker image infrastructure.
        delete_worker_base()

        logger.info('AMI creation complete. (%s)' % WORKER_AMI_ID)

        return WORKER_AMI_ID

    except EC2ResponseError as e:
        logger.error('Error creating the worker image, undoing...')

        # Try to undo all the changes.
        delete_worker_image()

        # Re-raise the error.
        raise e


def delete_worker_base():
    """
    Decommissions the infrastructure used to
    construct the worker image.
    """
    logger.info('Cleaning up worker image infrastructure...')
    ec2 = connect.ec2()

    # Terminate base instance.
    logger.info('Terminating base instance...')
    base_instances = ec2.get_all_instances(filters={'tag-key': 'name', 'tag-value': names['WORKER_IMAGE']})
    for reservation in base_instances:
        for i in reservation.instances:
            i.terminate()
        manage.wait_until_terminated(reservation.instances)

    # Delete security group.
    logger.info('Deleting the temporary security group...')
    manage.delete_security_group(names['WORKER_IMAGE'], purge=True)

    logger.info('Worker base instance cleanup complete.')


def delete_worker_image():
    """
    Deregisters the worker AMI and deletes its snapshot.
    """
    ec2 = connect.ec2()
    images = ec2.get_all_images(filters={'name': names['WORKER_IMAGE']})
    for image in images:
        image_id = image.id
        logger.info('Deleting worker image with id %s' % image_id)
        try:
            try:
                ec2.deregister_image(image_id, delete_snapshot=True)

            # If the snapshot doesn't exist, just try deregistering the image.
            except AttributeError as e:
                ec2.deregister_image(image_id)

        except EC2ResponseError as e:
            logger.warning('Could not deregister the image. It may already be deregistered.')


def group_exists():
    """
    Checks if the AutoScale Group exists.

    Returns:
        | int   -- number of AutoScale Groups found.
    """
    asg = connect.asg()

    groups = asg.get_all_groups(names=[names['AG']])
    return len(groups)



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

    # Copy over config files into the Salt state tree.
    logger.info('Copying config files to the Salt state tree...')
    cluster_config = get_filepath('config.ini')
    app_config = get_filepath('../config.py')
    celery_config = get_filepath('celery_config.py')
    configs = [cluster_config, app_config, celery_config]
    for config in configs:
        subprocess.Popen([
            'cp',
            config,
            os.path.join(salt_path, 'salt/deploy/')
        ])

    # Wait for SSH to become active...
    time.sleep(10)

    # Copy over Salt state tree to the host.
    # First have to move to a temporary directory.
    # '-o StrictHostKeyChecking no' automatically adds
    # the instance to SSH known hosts.
    logger.info('Secure copying Salt state tree to /tmp/salt on the instance...')
    command.scp(salt_path, '/tmp/salt', host=host, user=user, key=keyfile)

    # Move it to the real directory.
    logger.info('Moving Salt state tree to /srv/salt on the instance...')
    command.ssh(['sudo', 'mv', '/tmp/salt/*', '/srv'], host=host, user=user, key=keyfile)

    # Clean up the deploy keys files.
    logger.info('Cleaning up deploy keys... ')
    for key in deploy_keys:
        subprocess.Popen([
            'rm',
            os.path.join(salt_path, 'salt/deploy/', key)
        ])

    # Clean up the config files.
    logger.info('Cleaning up config files...')
    for config in configs:
        config = os.path.basename(config)
        subprocess.Popen([
            'rm',
            os.path.join(salt_path, 'salt/deploy/', config)
        ])

