Shallow Thought
===============

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

For more details, see [Detailed Setup](Detailed Setup).

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


