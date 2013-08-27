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


