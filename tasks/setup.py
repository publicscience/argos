"""
Cluster
==============

Setup workers for Celery.

Here, an EC2 AutoScale Group is used.

The following are created:
    * Elastic Load Balancer (with Health Check)
    * Launch Configuration
    * AutoScaling Group
    * Scaling Policies
    * CloudWatch MetricAlarm

And they can all also be dismantled.

Configuration is in `aws_config.py`.
"""

from . import aws_config as config
from boto.ec2.elb import ELBConnection, HealthCheck, LoadBalancer
from boto.ec2.autoscale import AutoScaleConnection, LaunchConfiguration, AutoScalingGroup, ScalingPolicy
from boto.ec2.cloudwatch import MetricAlarm
from boto.ec2.cloudwatch import connect_to_region as cloudwatch_connection
from boto.ec2 import connect_to_region as region_connection

# Load configuration.
REGION = config['REGION']
AG_NAME = config['AG_NAME']
LC_NAME = config['LC_NAME']
ELB_NAME = config['ELB_NAME']
AMI_IMAGE_ID = config['AMI_IMAGE_ID']
KEYPAIR_NAME = config['KEYPAIR_NAME']
ACCESS_KEY = config['AWS_ACCESS_KEY']
SECRET_KEY = config['AWS_SECRET_KEY']
SECURITY_GROUPS = config['SECURITY_GROUPS']


def commission():
    """
    Setup a new AutoScaling group,
    and everything else it needs.
    """

    conn = connect_as()
    conn_elb = connect_elb()

    # Get availability zones for region.
    conn_reg = region_connection(region_name=REGION)
    zones = [zone.name for zone in conn_reg.get_all_zones()]


    # Create the health check.
    health_check = HealthCheck(
                       'healthCheck',

                       # Seconds between health checks.
                       interval=20,

                       # The target of the health checks.
                       target='HTTP:80/index.html',

                       # Seconds to wait for ping response.
                       timeout=3
                   )


    # Create the load balancer.
    load_balancer = LoadBalancer(
                        name=ELB_NAME,
                        health_check=health_check,
                        availability_zones=zones,
                        connection=conn_elb
                    )

    # Create the load balancer on AWS.
    elb = conn_elb.create_load_balancer(load_balancer)
    # Point your site's CNAME here: elb.dns_name


    # Create the launch configuration.
    launch_config = LaunchConfiguration(
                        name=LAUNCH_CONFIG_NAME,

                        # AMI ID for autoscaling instances.
                        image_id=AMI_IMAGE_ID,

                        # The name of the EC2 keypair.
                        key_name=KEYPAIR_NAME,

                        # Security groups the instance will be in.
                        security_groups=SECURITY_GROUPS,

                        # Instance size.
                        instance_type='t1.micro',

                        # Enable monitoring (for CloudWatch).
                        instance_monitoring=True
                    )

    # Create the launch configuration on AWS.
    conn.create_launch_configuration(launch_config)


    # Create the autoscaling group.
    autoscaling_group = AutoScalingGroup(
                            group_name=AG_NAME,
                            load_balancers=[ELB_NAME],
                            availability_zones=zones,
                            launch_config=launch_config,
                            min_size=4,  # minimum group size
                            max_size=8,  # maximum group size
                            connection=conn
                        )

    # Create the autoscaling group on AWS.
    conn.create_auto_scaling_group(autoscaling_group)


    # Create the scaling policies.
    # These scaling policies change the size of the group.
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
    conn.create_scaling_policy(scale_up_policy)
    conn.create_scaling_policy(scale_dn_policy)

    # Some extra parameters are created on the policies
    # after they are created on AWS. We need to re-fetch them
    # to edit them.
    scale_up_policy = conn.get_all_policies(
                          as_group=AG_NAME,
                          policy_names=['scale_up']
                      )[0]
    scale_dn_policy = conn.get_all_policies(
                          as_group=AG_NAME,
                          policy_names=['scale_down']
                      )[0]

    # Create CloudWatch alarms.
    cloudwatch = cloudwatch_connection(REGION)

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


def decommission():
    """
    Dismantle the AutoScaling group,
    and everything else with it.
    """
    conn = connect_as()
    conn_elb = connect_elb()

    # Shutdown and delete autoscaling groups.
    groups = conn.get_all_groups(names=[AG_NAME])
    for group in groups:
        group.shutdown_instances()
        group.delete()

    # Delete launch configs.
    launch_configs = conn.get_all_launch_configurations(names=[LAUNCH_CONFIG_NAME])
    for lc in launch_configs:
        lc.delete()

    # Delete policies.
    conn.delete_policy('scale_down')
    conn.delete_policy('scale_up')

    # Delete alarms.
    cloudwatch = connect_to_region(REGION)
    cloudwatch.delete_alarms(['scale_up_on_cpu', 'scale_down_on_cpu'])

    # Delete the load balancer.
    conn_elb.delete_load_balancer(ELB_NAME)


def connect_as():
    """
    Create an AutoScale connection.
    """
    return AutoScaleConnection(ACCESS_KEY, SECRET_KEY)

def connect_elb():
    """
    Create an Elastic Load Balancer connection.
    """
    return ELBConnection(ACCESS_KEY, SECRET_KEY)
