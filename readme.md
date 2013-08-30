Shallow Thought
===============

## Setup
Make sure to setup & activate the `dev-env` virtualenv before you start:
```bash
$ virtualenv dev-env --no-site-packages
$ source dev-env/bin/activate
```

You may need to specify a Python 3 `virtualenv`, like so:
```bash
$ pip3 install virtualenv
$ virtualenv-3.3 env/dev --no-site-packages
$ source dev-env/bin/activate
```

Then you can install the dependencies:
```bash
(dev-env) $ pip install -r requirements.txt
```

Note that the `mwlib` package requires `libevent` on your computer.
On OSX, this can be installed with [Homebrew](http://brew.sh/):
```bash
$ brew install libevent
```

---

### Python 3 insanity
I have been trying to "future-proof" this project by building it in
Python 3. Unfortunately, many of the libraries do not yet officially
support Python 3.

These are libraries that do not currently support Python 3:
* NLTK – development for NLTK3.0, with Py3 support, is in progress.
* Boto – a Py3 branch is available.
* mrjob - no Py3 support available yet, but it is coming.
* mwlib - do not appear to be plans for Py3 support.
* readability-lxml - do not appear to be plans for Py3 support.

The latest version of NLTK, which supports Python 3, is installed via:
```bash
(dev-env) $ pip install git+git://github.com/nltk/nltk.git
```

For `mwlib`, I have put together an unofficial, minimal port 
([mwlib_simple](https://github.com/ftzeng/mwlib_simple)). This
port should provide all the needed functionality.

Prior to installation of this port, there are some dependencies:
```bash
(dev-env) $ brew install re2c
(dev-env) $ pip install cython
```

Then you can install this unofficial port like so:
```bash
(dev-env) $ git clone https://github.com/ftzeng/mwlib_simple.git
(dev-env) $ cd mwlib_simple
(dev-env) $ python setup.py install
(dev-env) $ cd .. && rm -rf mwlib_simple
```

You should be able to import and use the unofficial port like you would
the official library (limited to the parsing functions, of course).

`readability-lxml`, is relatively simple, so it is easy to port.
I have put together an [unofficial port](https://github.com/ftzeng/python-readability),
which can be installed like so:
```bash
(dev-env) $ pip install git+git://github.com/ftzeng/python-readability.git
```

[Boto](https://github.com/boto/boto), which is a dependency of [mrjob](https://github.com/Yelp/mrjob),
can have its [Python 3 branch](https://github.com/boto/boto/tree/py3kport) installed via:
```bash
(dev-env) $ pip install git+git://github.com/boto/boto.git@py3kport
```

#### NLTK
Usage of the NLTK library requires a few additional downloads.
Some of the libraries are *not* Python 3 ready, so you won't
be able to download all of the proper ones through the NLTK downloader
interface.

Instead, use the `do` script. You can install them all like so:
```bash
(dev-env) $ ./do setup nltk
```

---

### Python 2.7 parallel universe
*Note: Currently this env is not in use. I have opted for Celery instead
of MapReduce/mrjob for distributed Wiki processing. But MapReduce may
come in handy again for other processing later, so I'm leaving this in
for now.*

But for now, I will have Boto and mrjob running in a separate Python 2.7
environment. This environment will run and manage the mapreduce jobs.

It's pretty straightforward to setup this environment.
If you're in the `dev-env`, you need to first deactivate it:
```bash
(dev-env) $ deactivate
```

And then you can setup the env:
```bash
$ virtualenv-2.7 mr-env --no-site-packages
$ source mr-env/bin/activate
(mr-env) $ pip install -r mapreduce/requirements.txt
```

Because the NLTK data used in a Python 2.7 environment is different than
the data used in Python 3.3, you have to install that data separately.
This can be accomplished via:
```bash
(mr-env) $ ./do setup mapreduce
```

---

### MongoDB
To download and setup MongoDB, you can use the `do` script:
```bash
$ ./do setup mongo
```

Then, to run MongoDB:
```bash
$ ./do mongo
```
That will run MongoDB locally at port `27107`.

### Celery & RabbitMQ
[Celery](http://www.celeryproject.org/) is used for distributed
asynchronous tasks. It uses RabbitMQ as a broker (the server that
manages the message queue, which workers pick up jobs from.)

Celery and its dependencies should be installed with the
`requirements.txt`. You may run into trouble installing `pytz`; I wasn't
able to install it with pip. You can install it instead like so:
```bash
(dev-env) $ easy_install pytz
```

So you will also need `rabbitmq-server`. It also can be installed with Homebrew:
```bash
$ brew install rabbitmq
```
You will need to ensure that `/usr/local/sbin` is in your PATH; if it is
not, add the following to your `~/.bash_profile`:
```bash
export PATH="/usr/local/sbin:$PATH"
```

You can then start the RabbitMQ server with:
```bash
$ rabbitmq-server
```

You can start a Celery worker with the `do` script:
```bash
(dev-env) $ ./do worker
```

#### AWS
The `Cluster` module manages Celery and additionally provides
functionality to create an AWS EC2 AutoScaling Group on-demand
for distributed task processing.

Note that using AWS costs money! You pay for the EC2 instances' usage
and for [CloudWatch](https://aws.amazon.com/cloudwatch/) instance monitoring and alarms.

Note you will also need to configure `Adipose` accordingly, so that
your cluster computers have access to the database.

It requires some configuration before it can be used.
The config file is `cluster/aws_config.py` (there is a sample config
available that needs to be renamed to this). You will need to fill in
your AWS access key, secret key, and some other important info.

If you are signed up for AWS, you can create an access key and secret
key at the [Security
Credentials](https://console.aws.amazon.com/iam/home?#security_credential) page.

Set `AWS_ACCESS_KEY` and `AWS_SECRET_KEY` to these values.

You will also need to create a key pair, if you don't already have one,
for EC2. Go to the [EC2
Key Pairs panel](https://console.aws.amazon.com/ec2/#s=KeyPairs) and
select 'Create Key Pair'. Give it a name, and the keypair should
download. Make sure you secure its permissions:
```bash
$ chmod 400 /path/to/my/keypair.pem
```
And keep it in a safe place.

Set `KEYPAIR_NAME` to this key pair's name.

You also may need to create a new X.509 Certificate. This is also
accomplished in the [Security
Credentials](https://console.aws.amazon.com/iam/home?#security_credential) page.
Under 'X.509 Certificates', click 'Create New Certificate.' The private
key and certificate should both automatically download. Keep these in a
safe place.

You can create a new [security
group](https://console.aws.amazon.com/ec2/#s=SecurityGroups) if you want, or you can set `SECURITY_GROUPS` to `['default']` to use the default security group. Just make sure that your EC2 instances are all in the same security group!

Finally, you will need an AMI (Amazon Machine Image) ID, which can be
gathered through the [EC2 AMI
panel](https://console.aws.amazon.com/ec2/v2/#Images:). You can browse
existing AMIs [here at the AWS
marketplace](https://aws.amazon.com/amis). See below how to create your
own AMI.

You can additionally configure the names and region to your
requirements/liking.

##### Creating your own AMI
You can customize an existing AMI to your liking, and then save it as a
private AMI for your own usage. This is probably the easiest way.

For the cluster's use case, instance store-backed AMIs are fine, since
the data does not need to be persistent and the jobs will be infrequent
(so startup time is not an issue). The alternative, EBS-backed AMIs,
cost extra – the instances can be stopped instead of terminated (you
are able to restart it instead of having to create a new
instance), so they start up quicker, but you pay for the storage while it is stopped.

The process is:
* Create a [new EC2
instance](https://console.aws.amazon.com/ec2/#s=Instances) (click
'Launch Instance'). I created an Ubuntu Server 13.04 64-bit
t1.micro instance.
* Make note of the instance's Public DNS. It should be something like
`ec2-xxxxxxxxx.xxxxxxx.computer.amazonaws.com`.
* SSH into the instance once it is finished launching:

```bash
$ ssh -i /path/to/my/keypair.pem ubuntu@<public DNS>
```
* While SSH'd, you can start customizing the image. Install the
packages you need, etc.
* You will need your AWS Account Number. This can be found on your
[Account
Activity](https://portal.aws.amazon.com/gp/aws/developer/account/index.html?ie=UTF8&action=activity-summary) page.
It looks something like `1111-1111-1111`, but you want to remove the
dashes.
* You will also need your AWS access key, secret key, private key, and
X.509 certificate (see above on how to create these).
* On the instance, you need to create a directory to add your private
key and X.509 certificate. These files should *not* be part of the
image, so create a temporary directory that will be ignored by the image
creation process:

```bash
$ mkdir /tmp/cert
$ sudo chmod 777 /tmp/cert
```
* Now you can upload your private key and X.509 certificate to this
image. On your local machine:

```bash
$ scp -i /path/to/my/keypair.pem /path/to/my/privatekey.pem
/path/to/my/certificate.pem ubuntu@<public DNS>:/tmp/cert
```
* On the instance, you will need to install `ec2-ami-tools` if they
aren't already on the instance:

```bash
$ sudo apt-get install ec2-ami-tools
```
On the Ubuntu AMI that I used, `apt-get` needed access to `multiverse`
before this would work. To enable `multiverse`, edit
`etc/apt/sources.list` and uncomment the lines that end in `multiverse`.
Then run:

```bash
$ sudo apt-get update
```
and try the installation again.
* Now, on the instance, you can generate the image:

```bash
$ sudo su
$ ec2-bundle-vol -k /tmp/cert/<privatekey>.pem -c /tmp/cert/<cert>.pem
-u <account number w/o dashes> -e /tmp/cert
```
* You need to create an AWS [S3
bucket](https://console.aws.amazon.com/s3/) in the same region as your
instance. This is where the image will be stored.
* Now you can upload the image to S3:

```bash
$ ec2-upload-bundle -b <s3 bucket name> -m <manifest path> -a <your
access key> -s <your secret key>
```
* And now you can register the AMI:

```bash
$ ec2-register <s3 bucket name>/<path>/<manifest file>.xml -n <what to
name the image> -O <your access key> -W <your secret key>
```

## Deployment
Generate [SSH deploy
keys](https://help.github.com/articles/managing-deploy-keys) for this repository, and specify the path to them in
`cluster/aws_config.py`.


## Documentation
To generate documentation, do:
```bash
(dev-env) $ ./do doc
```

The documentation will be located at `doc/_build/html/index.html`.

## Testing
To run the tests:
```bash
(dev-env) $ nosetests tests
```

## Profiling and Performance
Some profiling for the `WikiDigester` is available in `profiler.py`; run
it like so:
```bash
$ (dev-env) python profiler.py
```
After some quick profiling, the hangup is in `Brain.count`. In particular,
it is the lemmatization that takes up the most time. 
The profiler wiki data is 384KB. With lemmatization, it takes about 5.45
seconds to process. Without, it takes only about 1.14 seconds.

The full enwiki pages-articles dump is about 44.9GB. Which is about
116927 times the amount of the profiler wiki data. With lemmatization,
a rough estimate for completion is ~637252s ≈ 7 days, 9 hours.
Without lemmatization, it is roughly 133297s ≈ 1 day, 13 hours.

Turning wikidigestion into a distributed process should save a lot of
time.

## The Future (To Do)
* Perhaps the main area of future refinement will be all parts relating
to text processing and analysis.

## Modules
### Membrane (in progress)
The `Membrane` will provide a single common interface to external APIs, such as
Twitter, and to RSS feeds (via
        [Feedparser](http://pythonhosted.org/feedparser/introduction.html)).
Twitter integration will be provided by
[Tweepy](https://github.com/tweepy/tweepy), and content extraction for
feeds will be provided by
[Readability](https://github.com/buriy/python-readability). Twitter
support will probably be excluded from MVP/V1.0.

### Digester
The `Digester` manages the XML parsing. It is a superclass of the
`WikiDigester`.

The `Digester` also includes:

#### Gullet
The `Gullet` provides a general means of downloading remote files. In
the case of the Digester, it downloads the latest Wikipedia dumps. It is
capable of resuming downloads if the server supports it.

### Adipose
The `Adipose` provides an common interface to a data-persistence store, i.e. a
database. In its current implementation, this database is MongoDB. It's
purpose is to provide some flexibility with the database. That is, a
different database could be swapped in while keeping the Adipose
interface the same. In the present use case, it will provide a means
of storing the parsed and processed information into MongoDB.

### Brain (in progress)
The `Brain` provides the text processing functionality, so it functions
mostly as a wrapper for NLTK. It provides parsing functionality such as
tokenization, lemmatization, and frequency distribution.

### WikiDigester (in progress)
The `WikiDigester` is a subclass of the `Digester` and is essentially a
Digester designed to specifically handle Wikipedia dumps. As such, it
has some special functionality tailored to this.

### Memory (in progress)
The `Memory` provides an interface to Solr. The actual Solr instance
still needs to be ported in with a proper Solr configuration (see
[Parrott](https://github.com/ftzeng/parrott)).


