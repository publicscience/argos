Shallow Thought
===============

Please consult the
[wiki](https://github.com/publicscience/shallowthought/wiki) for more information.

## Quick Setup

The setup process for Shallow Thought is fairly complex, but some scripts vastly simplify it.

*Note: In addition to this initial setup, you will need to [configure
AWS](AWS Setup) so that distributed processing works.*

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
