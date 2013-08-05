Shallow Thought
===============

## Setup
Make sure to setup & activate the virtualenv before you start:
```bash
$ virtualenv shallowthought-env --no-site-packages
$ source shallowthought-env/bin/activate
```

Then you can install the dependencies:
```bash
$ pip install -r requirements.txt
```

Note that the `mwlib` package requires `libevent` on your computer.
On OSX, this can be installed with [Homebrew](http://brew.sh/):
```bash
$ brew install libevent
```

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
Documentation is located at `doc/_build/html/index.html`.

To generate documentation, do:
```bash
$ cd doc
$ make clean && make html
```

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

### Digester (in progress)
The `Digester` manages the Wikipedia knowledge base. The core module
will handle the parsing of the Wikipedia XML dump, with the help of
[mwlib](https://github.com/pediapress/mwlib). This parsing includes some
NLP processing, including tokenization, lemmatization, and frequency
distribution.

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
mostly as a wrapper for NLTK.

### WikiDigester (in progress)
The `WikiDigester` is a subclass of the `Digester` and is essentially a
Digester designed to specifically handle Wikipedia dumps. As such, it
has some special functionality tailored to this.


