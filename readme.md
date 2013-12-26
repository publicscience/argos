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

Then, the easiest way to set things up is to just run the `setup` script:
```bash
$ ./setup
```
This will install any necessary system dependencies, setup the
virtualenv, setup NLTK with the necessary data, download and setup
MongoDB, download and setup [Stanford NER](http://nlp.stanford.edu/software/CRF-NER.shtml#Download), and generate the documentation.

### Running & Development
And then when you're ready to start developing/testing, run:
```bash
$ ./go &
```
This command will startup the Argos environment as a background process.
It will tell you its `pid`, keep note of that so you can kill it later.
The environment runs:
* MongoDB
* A Celery worker
* RabbitMQ
* Redis
* Stanford NER

Then when you're done, kill it with:
```bash
$ kill <pid>
```


# AWS Setup
You will also need to set up Amazon Web Services to adminster and use
clusters. See [AWS
Setup](https://github.com/publicscience/argos/wiki/AWS-Setup)
