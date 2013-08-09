Shallow Thought
===============

## Setup
Make sure to setup & activate the virtualenv before you start:
```bash
$ virtualenv shallowthought-env --no-site-packages
$ source shallowthought-env/bin/activate
```

You may need to specify a Python 3 `virtualenv`, like so:
```bash
$ pip3 install virtualenv
$ virtualenv-3.3 shallowthought-env --no-site-packages
$ source shallowthought-env/bin/activate
```

Then you can install the dependencies:
```bash
(shallowthought-env) $ pip install -r requirements.txt
```

Since NLTK3.0 (which has Python 3 support) is still in development,
you will likely need to install that separately:
```bash
(shallowthought-env) $ pip install git+git://github.com/nltk/nltk.git
```

Note that the `mwlib` package requires `libevent` on your computer.
On OSX, this can be installed with [Homebrew](http://brew.sh/):
```bash
$ brew install libevent
```
Note: `mwlib` is not currently being used. It does not support Python 3.

## MongoDB
To setup and run MongoDB ([download](http://www.mongodb.org/downloads)):
```bash
$ cd /path/to/mongodb/download
$ ./bin/mongod
```
That will run MongoDB locally at port `27107`.

## NLTK
Usage of the NLTK library requires a few additional downloads. NLTK's
download interface can be accessed like so:

```bash
$ python
>>> import nltk
>>> nltk.download()
```

The necessary packages are:
* Punkt
* WordNet


## Documentation
To generate documentation, do:
```bash
$ cd doc
$ make clean && make html
```

The documentation will be located at `doc/_build/html/index.html`.

## Testing
To run the tests:
```bash
$ nosetests
```

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


