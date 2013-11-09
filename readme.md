Argos
===============

Please consult the
[wiki](https://github.com/publicscience/argos/wiki) for detailed information.

# Quick Setup

The setup process for Argos is fairly complex, but some scripts vastly simplify it.

Argos is built in Python 3.3, so make sure you have `pip3` and `virtualenv-3.3`:
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
./do setup
```
This will install any necessary system dependencies, setup the
virtualenv, setup NLTK with the necessary data, download and setup
MongoDB, download and setup [Stanford NER](http://nlp.stanford.edu/software/CRF-NER.shtml#Download), and generate the documentation.

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
* Stanford NER
* Bash


# AWS Setup
You will also need to set up Amazon Web Services to adminster and use
clusters. See [AWS
Setup](https://github.com/publicscience/argos/wiki/AWS-Setup)
