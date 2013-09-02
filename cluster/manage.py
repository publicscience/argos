"""
Cluster
==============

Setup workers for Celery.

Here, an EC2 AutoScale Group is used.

The following are created:
    * Security Group
    * Elastic Load Balancer (with Health Check)
    * Launch Configuration
    * AutoScaling Group
    * Scaling Policies
    * CloudWatch MetricAlarms

And they can all also be dismantled.

Configuration is in `aws_config.py`.
"""

from boto.ec2.elb import ELBConnection, HealthCheck, LoadBalancer
from boto.ec2.autoscale import AutoScaleConnection, LaunchConfiguration, AutoScalingGroup, ScalingPolicy
from boto.ec2.cloudwatch import MetricAlarm
from boto.ec2.cloudwatch import connect_to_region as cw_connect_to_region
from boto.ec2 import connect_to_region

import os, time, subprocess, base64
from string import Template

# Logging
from logger import logger
logger = logger(__name__)

# Load configuration.
from cluster import aws_config as c
REGION = c.REGION
NAME = c.CLUSTER_NAME
INSTANCE_USER = c.INSTANCE_USER
ACCESS_KEY = c.AWS_ACCESS_KEY
SECRET_KEY = c.AWS_SECRET_KEY
KEYPAIR_NAME = c.KEYPAIR_NAME
PATH_TO_KEY = c.PATH_TO_KEY
PATH_TO_DEPLOY_KEYS = c.PATH_TO_DEPLOY_KEYS
BASE_AMI_ID = c.BASE_AMI_ID
LB_NAME = '%s-loadbalancer' % NAME
LC_NAME = '%s-launchconfig' % NAME
HC_NAME = '%s-healthcheck' % NAME
AG_NAME = '%s-autoscale' % NAME
SG_NAME = '%s-security' % NAME
MASTER_NAME = '%s-master' % NAME

def commission():
    """
    Setup a new cluster.
    """

    logger.info('Commissioning new cluster...')

    # Check to see if the AutoScale Group already exists.
    if status():
        logger.info('The AutoScale Group already exists, exiting!')
        return

    conn_asg = _connect_asg()
    conn_elb = _connect_elb()
    conn_ec2 = _connect_ec2()

    # Get availability zones for region.
    zones = [zone.name for zone in conn_ec2.get_all_zones()]

    # Create a new security group.
    logger.info('Creating the security group (%s)...' % SG_NAME)
    sec_group = conn_ec2.create_security_group(SG_NAME, 'The cluster security group.')

    # Authorize the instances in the group to communicate with each other.
    sec_group.authorize(src_group=sec_group)

    # Authorize HTTP access.
    sec_group.authorize('tcp', 80, 80, '0.0.0.0/0')

    # Authorize SSH access (temporarily).
    logger.info('Temporarily enabling SSH access to master instance...')
    sec_group.authorize('tcp', 22, 22, '0.0.0.0/0')

    # Create the Salt Master/RabbitMQ/MongoDB server.
    logger.info('Creating the master instance (%s)...' % MASTER_NAME)
    master_init_script = _load_script('setup_master.sh')
    reservations = conn_ec2.run_instances(
                       BASE_AMI_ID,
                       key_name=KEYPAIR_NAME,
                       security_groups=[SG_NAME],
                       instance_type='m1.small',
                       user_data=master_init_script
                   )
    instance = reservations.instances[0]

    # Wait until the instance is ready.
    logger.info('Waiting for master instance to launch...')
    istatus = instance.update()
    while istatus == 'pending':
        time.sleep(10)
        istatus = instance.update()
    logger.info('Master instance has launched. Configuring...')

    # Tag the instance with a name so we can find it later.
    instance.add_tag('name', MASTER_NAME)


    # Setup master instance with the Salt state tree.

    # NOTE: Fabric does not yet support Py3.3.
    # Keeping this in until it does...
    # Set the host for Fabric to connect to.
    #env.hosts = [instance.public_dns_name]
    #env.user = INSTANCE_USER
    #env.key_filename = PATH_TO_KEY

    # For now, using subprocess Popen and call.
    # Not sure if this is really the best solution...
    env = {
            'host': instance.public_dns_name,
            'user': INSTANCE_USER,
            'key_filename': _get_filepath(PATH_TO_KEY)
    }

    # Copy over deploy keys into the Salt state tree.
    logger.info('Copying deploy keys to the Salt state tree...')
    salt_path = _get_filepath('salt/')
    deploy_keys_path = _get_filepath(PATH_TO_DEPLOY_KEYS)
    deploy_keys = ['id_rsa', 'id_rsa.pub']
    for key in deploy_keys:
        subprocess.Popen([
            'cp',
            os.path.join(deploy_keys_path, key),
            os.path.join(salt_path, 'salt/deploy/')
        ])

    # Copy over Salt state tree to Master.
    # First have to move to a temporary directory.
    # '-o StrictHostKeyChecking no' automatically adds
    # the instance to SSH known hosts.
    logger.info('Secure copying Salt state tree to /tmp/salt on the master instance...')

    # Wait for SSH to become active...
    time.sleep(10)

    print('TRYING TO SSH')
    print(env['key_filename'])
    print(salt_path)
    print('%s@%s:/tmp/salt' % (env['user'], env['host']))

    scp = [
            'scp',
            '-r',
            '-o',
            'StrictHostKeyChecking=no',
            '-i',
            env['key_filename'],
            salt_path,
            '%s@%s:/tmp/salt' % (env['user'], env['host'])
    ]

    # Get output from the command to check for errors.
    results = subprocess.Popen(scp, stderr=subprocess.PIPE).communicate()

    # Check if we couldn't connect, and try again.
    while b'Connection refused' in results[1]:
        results = subprocess.Popen(scp, stderr=subprocess.PIPE).communicate()


    # Move it to the real directory.
    logger.info('Moving Salt state tree to /srv/salt on the master instance... ')
    subprocess.call([
        'ssh',
        '-t',
        '-i',
        env['key_filename'],
        '%s@%s' % (env['user'], env['host']),
        'sudo',
        'mv',
        '/tmp/salt',
        '/srv'
    ])

    # Disable SSH access.
    logger.info('Disabling SSH access to master instance...')
    sec_group.revoke('tcp', 22, 22, '0.0.0.0/0')

    # Clean up the deploy keys.
    logger.info('Cleaning up deploy keys... ')
    for key in deploy_keys:
        subprocess.Popen([
            'rm',
            os.path.join(salt_path, 'salt/deploy/', key)
        ])



    # Replace the $salt_master var in the raw Minion init script with the Master DNS name,
    # so Minions will know where to connect to.
    minion_init_script = _load_script('setup_minion.sh', master_dns=instance.private_dns_name)

    # Create the health check.
    logger.info('Creating the health check (%s)...' % HC_NAME)
    health_check = HealthCheck(
                       HC_NAME,

                       # Seconds between health checks.
                       interval=20,

                       # The target of the health checks.
                       target='HTTP:80/index.html',

                       # Seconds to wait for ping response.
                       timeout=3
                   )


    # Create the load balancer.
    logger.info('Creating the load balancer (%s)...' % LB_NAME)
    load_balancer = conn_elb.create_load_balancer(
                        LB_NAME,
                        zones,
                        listeners=[(80, 80, 'http'), (443, 443, 'tcp')]
                    )
    load_balancer.configure_health_check(health_check)
    # Point your site's CNAME here: load_balancer.dns_name


    # Create the launch configuration.
    logger.info('Creating the launch configuration (%s)...' % LC_NAME)
    launch_config = LaunchConfiguration(
                        name=LC_NAME,

                        # AMI ID for autoscaling instances.
                        image_id=BASE_AMI_ID,

                        # The name of the EC2 keypair.
                        key_name=KEYPAIR_NAME,

                        # User data;
                        # the initialization script for the instances.
                        user_data=minion_init_script,

                        # Security groups the instance will be in.
                        security_groups=[SG_NAME],

                        # Instance size.
                        instance_type='m1.small',

                        # Enable monitoring (for CloudWatch).
                        instance_monitoring=True
                    )

    # Create the launch configuration on AWS.
    conn_asg.create_launch_configuration(launch_config)


    # Create the autoscaling group.
    logger.info('Creating the autoscaling group (%s)...' % AG_NAME)
    autoscaling_group = AutoScalingGroup(
                            group_name=AG_NAME,
                            load_balancers=[LB_NAME],
                            availability_zones=zones,
                            launch_config=launch_config,
                            min_size=2,  # minimum group size
                            max_size=8,  # maximum group size
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
    conn_elb = _connect_elb()
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
            while len(group_instances) > 0:
                time.sleep(10)
                group_instances = [i for i in group_instances if i.update() != 'terminated']

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

    # Delete the load balancer.
    logger.info('Deleting the load balancer (%s)...' % LB_NAME)
    conn_elb.delete_load_balancer(LB_NAME)

    # Delete the master instance(s).
    logger.info('Deleting the master instance (%s)...' % MASTER_NAME)
    master_instances = conn_ec2.get_all_instances(filters={'tag-key': 'name', 'tag-value': MASTER_NAME})
    for reservation in master_instances:
        for i in reservation.instances:
            i.terminate()
            istatus = i.update()
            while istatus == 'shutting-down':
                time.sleep(10)
                istatus = i.update()

    # Delete the security group.
    logger.info('Deleting the security group (%s)...' % SG_NAME)
    conn_ec2.delete_security_group(name=SG_NAME)

    logger.info('Decommissioning complete.')



def status():
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

    Returns:
        | AutoScaleConnection
    """
    return AutoScaleConnection(ACCESS_KEY, SECRET_KEY)


def _connect_ec2():
    """
    Creates an EC2 connection.

    Returns:
        | EC2Connection
    """
    return connect_to_region(
                REGION,
                aws_access_key_id=ACCESS_KEY,
                aws_secret_access_key=SECRET_KEY
           )


def _connect_elb():
    """
    Create an Elastic Load Balancer connection.

    Returns:
        | ELBConnection
    """
    return ELBConnection(ACCESS_KEY, SECRET_KEY)


def _connect_clw():
    """
    Creates a CloudWatch connection.

    Returns:
        | CloudWatchConnection
    """
    return cw_connect_to_region(
                    REGION,
                    aws_access_key_id=ACCESS_KEY,
                    aws_secret_access_key=SECRET_KEY
                 )


def _load_script(filename, **kwargs):
    """
    Loads a script from this directory as bytes.
    This script will be passed as `user-data`.

    Args:
        | filename (str)    -- the filename or path of the script to open.
        | **kwargs          -- optional keyword arguments of a variable and
                            the value to replace it with in the script.

    When you specify `**kwargs`, say `foo=bar`, then every instance of ``$foo`
    will be replaced with `bar`.
    """
    script = open(_get_filepath(filename), 'r').read()

    # Substitute for specified vars.
    if kwargs:
        script = Template(script).substitute(**kwargs)

    # Turn into bytes.
    return script.encode('utf-8')

def _get_filepath(filename):
    """
    Gets filepath for a file
    relative to this directory.
    """
    dir = os.path.dirname(__file__)
    return os.path.abspath(os.path.join(dir, filename))
