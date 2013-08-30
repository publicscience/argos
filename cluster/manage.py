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
from boto.ec2.cloudwatch import MetricAlarm, CloudWatchConnection
from boto.ec2 import EC2Connection

from string import Template

# Logging
from logger import logger
logger = logger(__name__)

# Load configuration.
from cluster import aws_config as c
REGION = c.REGION
NAME = c.CLUSTER_NAME
ACCESS_KEY = c.AWS_ACCESS_KEY
SECRET_KEY = c.AWS_SECRET_KEY
KEYPAIR_NAME = c.KEYPAIR_NAME
BASE_AMI_ID = c.BASE_AMI_ID
AMI_ID = c.AMI_ID
LB_NAME = '%s_loadbalancer' % NAME
LC_NAME = '%s_launchconfig' % NAME
HC_NAME = '%s_healthcheck' % NAME
AG_NAME = '%s_autoscale' % NAME
SG_NAME = '%s_security' % NAME
MASTER_NAME = '%s_master' % NAME
MINION_INIT_SCRIPT_RAW = open('setup_minion.sh').read()
MASTER_INIT_SCRIPT = open('setup_master.sh').read()

def commission():
    """
    Setup a new cluster.
    """

    logger.info('Commissioning new cluster...')

    # Check to see if the AutoScale Group already exists.
    if status():
        logger.info('The AutoScale Group already exists, exiting!')
        return

    conn_asg = connect_asg()
    conn_elb = connect_elb()
    conn_ec2 = connect_ec2()

    # Get availability zones for region.
    zones = [zone.name for zone in conn_ec2.get_all_zones()]

    # Create a new security group.
    logger.info('Creating the security group (%s)...' % SG_NAME)
    sec_group = conn_ec2.create_security_group(SG_NAME, 'The cluster security group.')

    # Authorize the instances in the group to communicate with each other.
    sec_group.authorize(src_group=sec_group)

    # Authorize HTTP access.
    sec_group.authorize('tcp', 80, 80, '0.0.0.0/0')

    # Authorize SSH access.
    # This is an example! Probably don't want to allow SSH from anywhere.
    #web.authorize('tcp', 22, 22, '0.0.0.0/0')
    #web.revoke('tcp', 22, 22, '0.0.0.0/0')

    # Create the Salt Master/RabbitMQ/MongoDB server.
    logger.info('Creating the master instance (%s)...' % MASTER_NAME)
    reservations = conn_ec2.run_instances(
                       BASE_AMI_ID,
                       key_name=KEYPAIR_NAME,
                       security_groups=[SECURITY_GROUP_NAME],
                       instance_type='m1.small',
                       user_data=MASTER_INIT_SCRIPT
                   )

    # Tag the instance with a name so we can find it later.
    instance = reservations.instances[0]
    instance.add_tag('name', MASTER_NAME)

    # Get info to connect to the instance.
    instance_public_dns = instance.public_dns_name
    instance_public_ip = instance.ip_address

    # Setup the Master server with Salt Master, RabbitMQ, and MongoDB.


    # Replace the $salt_master var in the raw Minion init script with the Master DNS name,
    # so Minions will know where to connect to.
    MINION_INIT_SCRIPT = Template(MINION_INIT_SCRIPT_RAW).substitute(salt_master=instance.private_dns_name)


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
                        [(80, 80, 'http'), (443, 443, 'tcp')]
                    )
    load_balancer.configure_health_check(health_check)
    # Point your site's CNAME here: load_balancer.dns_name


    # Create the launch configuration.
    logger.info('Creating the launch configuration (%s)...' % LC_NAME)
    launch_config = LaunchConfiguration(
                        name=LC_NAME,

                        # AMI ID for autoscaling instances.
                        image_id=AMI_ID,

                        # The name of the EC2 keypair.
                        key_name=KEYPAIR_NAME,

                        # User data;
                        # the initialization script for the instances.
                        user_data=MINION_INIT_SCRIPT,

                        # Security groups the instance will be in.
                        security_groups=[SECURITY_GROUP_NAME],

                        # Instance size.
                        instance_type='t1.micro',

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
                          name='scale_up',
                          adjustment_type='ChangeInCapacity',
                          as_name=AG_NAME,
                          scaling_adjustment=1, # instances to add
                          cooldown=180
                      )
    scale_dn_policy = ScalingPolicy(
                          name='scale_down',
                          adjustment_type='ChangeInCapcity',
                          as_name=AG_NAME,
                          scaling_adjustments=-1, # instances to remove
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
                          policy_names=['scale_up']
                      )[0]
    scale_dn_policy = conn_asg.get_all_policies(
                          as_group=AG_NAME,
                          policy_names=['scale_down']
                      )[0]

    # Create CloudWatch alarms.
    logger.info('Creating CloudWatch MetricAlarms...')
    cloudwatch = CloudWatchConnection(
                    region_name=REGION,
                    aws_access_key_id=ACCESS_KEY,
                    aws_secret_access_key=SECRET_KEY
                 )

    # We need to specify the "dimensions" of this alarm,
    # which describes what it watches (here, the whole autoscaling group).
    alarm_dimensions = {'AutoScalingGroupName': AG_NAME}

    # Create the scale up alarm.
    # Scale up when average CPU utilization becomes greater than 70%.
    scale_up_alarm = MetricAlarm(
                        name='scale_up_on_cpu',
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
                        name='scale_down_on_cpu',
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

    conn_asg = connect_asg()
    conn_elb = connect_elb()
    conn_ec2 = connect_ec2()

    # Shutdown and delete autoscaling groups.
    groups = conn_asg.get_all_groups(names=[AG_NAME])
    for group in groups:
        group.shutdown_instances()
        group.delete()

    # Delete launch configs.
    launch_configs = conn_asg.get_all_launch_configurations(names=[LC_NAME])
    for lc in launch_configs:
        lc.delete()

    # Delete policies.
    conn_asg.delete_policy('scale_down')
    conn_asg.delete_policy('scale_up')

    # Delete alarms.
    cloudwatch = CloudWatchConnection(
                    region_name=REGION,
                    aws_access_key_id=ACCESS_KEY,
                    aws_secret_access_key=SECRET_KEY
                 )
    cloudwatch.delete_alarms(['scale_up_on_cpu', 'scale_down_on_cpu'])

    # Delete the load balancer.
    conn_elb.delete_load_balancer(LB_NAME)

    # Delete the master instance.
    master_id = conn_ec2.get_all_reservations(filters={'name': MASTER_NAME})[0]
    conn_ec2.terminate_instances([master_id])

    # Delete the security group.
    conn_ec2.delete_security_group(name=SECURITY_GROUP_NAME)

    logger.info('Decommissioning complete.')


def status():
    """
    Checks if the AutoScale Group exists.

    Returns:
        | int   -- number of AutoScale Groups found.
    """
    conn_asg = connect_asg()

    groups = conn_asg.get_all_groups(names=[AG_NAME])
    return len(groups)


def connect_asg():
    """
    Create an AutoScale Group connection.

    Returns:
        | AutoScaleConnection
    """
    return AutoScaleConnection(ACCESS_KEY, SECRET_KEY)

def connect_ec2():
    """
    Creates an EC2 connection.

    Returns:
        | EC2Connection
    """
    return EC2Connection(
                region_name=REGION,
                aws_access_key_id=ACCESS_KEY,
                aws_secret_access_key=SECRET_KEY
           )

def connect_elb():
    """
    Create an Elastic Load Balancer connection.

    Returns:
        | ELBConnection
    """
    return ELBConnection(ACCESS_KEY, SECRET_KEY)
