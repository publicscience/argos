Argos
===============

![Argos](https://raw.github.com/wiki/publicscience/argos/img/argos.png)

Please consult the
[wiki](https://github.com/publicscience/argos/wiki) for detailed information.

# 0 to Argos

*Note: In addition to this initial setup, you will need to [[configure
AWS|AWS-Setup]] so that distributed processing works.*

The setup process for Argos is fairly complex, but some scripts vastly simplify it.

Argos is built in Python 3.3, so make sure you have `pip3` and `virtualenv-3.3`:
```bash
# OSX
$ brew install python3 # (also installs pip3)
$ pip3 install virtualenv

# Ubuntu
$ sudo apt-get install python3.3 python3-pip -y
$ sudo pip3 install virtualenv
```

Then, the easiest way to set things up is to just run the `setup` script:
```bash
$ ./setup
```
This will install any necessary system dependencies, setup the
virtualenv, setup NLTK with the necessary data, install Postgres and setup its databases,
download and setup [Stanford NER](http://nlp.stanford.edu/software/CRF-NER.shtml#Download), and generate the documentation.

### Running & Development
And then when you're ready to start developing/testing, run:
```bash
$ ./go &
```
This command will startup the Argos environment as a background process.
It will tell you its `pid`, keep note of that so you can kill it later.
The environment runs:
* Redis (6379)
* Stanford NER (8080)
* RabbitMQ (5672)
* A Celery worker

*Note: If you're running this on Ubuntu, some of these processes may
fail, but it is because they are already running as services. Don't
worry about it.*

Then when you're done, kill it with:
```bash
$ kill <pid>
```

### Tests, Performance, Evaluation
When you get everything setup it's worth running the tests to ensure
that things have installed correctly:
```
$ source dev-env/bin/activate
$ ./manage test
```

You can also profile some of the more intensive parts to identify
bottlenecks:
```
$ source dev-env/bin/activate
$ ./manage profile
```

You can also evaluate the quality of some of the algorithms, such as
clustering:
```
$ source dev-env/bin/activate
$ ./manage evaluate
```

*Note: If you are having import errors or the packages seem to be
missing, fear not ~ it may be because some package failed to install and
pip rolled back the installs of everything else. Check your pip logs at
`~/.pip/pip.log`. I'd wager it is `scipy` which ran into a missing
dependency.*

You can optionally setup the default ~436 sources for collecting
articles by doing (make sure Postgres is running):
```bash
$ ./manage/load_sources
```


# AWS Setup
You will also need to set up Amazon Web Services to adminster and use
cloud instances. See [AWS
Setup](https://github.com/publicscience/argos/wiki/AWS-Setup)
