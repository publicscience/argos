Shallow Thought
===============

Please consult the
[wiki](https://github.com/publicscience/shallowthought/wiki) for detailed information.

# Quick Setup

The setup process for Shallow Thought is fairly complex, but some scripts vastly simplify it.

Shallow Thought is built in Python 3.3, so make sure you have `pip3` and `virtualenv-3.3`:
```bash
# OSX
$ brew install python3 # (also installs pip3)
$ pip3 install virtualenv

# Ubuntu
$ sudo apt-get install python3.3
$ sudo apt-get install python3-pip
$ pip-3.3 install virtualenv
```

Then, the easiest way to set things up is to just run the `do` script:
```bash
./do setup all
```
This will install any necessary system dependencies, setup the
virtualenv, setup NLTK with the necessary data, download and setup
MongoDB, and generate the documentation.

*Note: You may run into trouble installing the `pytz` package. If you
do, install it like so: `easy_install pytz` while `dev-env` is activated.*

### Running & Development
And then when you're ready to start developing/testing, run:
```bash
./do go
```
This command will startup a `screen` session with four windows running:
* MongoDB
* A Celery worker
* RabbitMQ
* Bash

### The MapReduce environment
Note that this setup task does *not* setup the MapReduce environment, which is
separate because it requires Python 2.7. It is not currently being used,
but if you want to install it, you can additionally run:
```bash
$ ./do setup mapreduce
```

# AWS Setup

Shallow Thought makes use of Amazon Web Services (AWS) for its distributed processing of Wikipedia dumps.

*Note that using AWS costs money! You pay for the EC2 instances' usage
and for [CloudWatch](https://aws.amazon.com/cloudwatch/) instance monitoring and alarms.*

The `Cluster` module manages Celery and additionally provides
functionality to create an AWS EC2 AutoScaling Group on-demand
for distributed task processing.

It requires some configuration before it can be used.
The config file is `cluster/aws_config.py` (there is a sample config
available that needs to be renamed to this). You will need to fill in
your AWS access key, secret key, and some other important info.

## Access Key and Secret Key
`AWS_ACCESS_KEY` and `AWS_SECRET_KEY`

If you are signed up for AWS, you can create an access key and secret
key at the [Security
Credentials](https://console.aws.amazon.com/iam/home?#security_credential) page.

Set `AWS_ACCESS_KEY` and `AWS_SECRET_KEY` to these values.

## Key Pair
`KEYPAIR_NAME` and `PATH_TO_KEY`

You will also need to create a key pair, if you don't already have one,
for EC2. Go to the [EC2
Key Pairs panel](https://console.aws.amazon.com/ec2/#s=KeyPairs) and
select 'Create Key Pair'. Give it a name, and the keypair should
download. Make sure you secure its permissions:
```bash
$ chmod 400 /path/to/my/key.pem
```
And keep it in a safe place.

Set `KEYPAIR_NAME` to this key pair's name.
Set `PATH_TO_KEY` so that it points to the location of your key.

## Deploy Keys
`PATH_TO_DEPLOY_KEYS`

You will also need a set of deploy keys so that instances have access to
Shallow Thought's git repository (so they can grab the necessary files).

You can create a new set like so:
```bash
$ ssh-keygen -t rsa -C "youremail@email.com"
```
Which by default generates `~/.ssh/id_rsa` and `~/.ssh/id_rsa.pub`.

I believe you want to create the keys *without* a password so that one
is not required to use them.

You can add the deploy key to your Github repository by following the
[instructions
here](https://help.github.com/articles/managing-deploy-keys#deploy-keys).

Set `PATH_TO_DEPLOY_KEYS` to the directory that these keys are contained
in.


## AMI
`BASE_AMI_ID` and `INSTANCE_USER`

Finally, you will need an AMI (Amazon Machine Image) ID, which
determines what image to create new instances out of.

Shallow Thought is preconfigured to use an `Ubuntu 13.04 64-bit
us-east-1 instance-store` image. If you are operating in a different region,
you will need to change this to an image of the appropriate region.
You can find one for your region at the [Ubuntu AMI listing](https://cloud-images.ubuntu.com/locator/ec2/).

If you're sticking with Ubuntu (and you should), you will not need to
change the `INSTANCE_USER` value. If you're not, update it to be the
appropriate user for that image.

Set `BASE_AMI_ID` to the AMI ID.

## Name and Region
`CLUSER_NAME` and `REGION`

You can additionally configure the cluster name and region to your
requirements/liking. If you are using a region other than `us-east-1`,
remember to change `BASE_AMI_ID`.
