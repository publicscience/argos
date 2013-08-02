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

## Testing
To run the tests:
```bash
$ nosetests
```

## MongoDB
To setup and run MongoDB ([download](http://www.mongodb.org/downloads)):
```bash
$ cd /path/to/mongodb/download
$ ./bin/mongod
```
That will run MongoDB locally at port `27107`.

## Documentation
Documentation is located at `doc/_build/html/index.html`.

To generate documentation, do:
```bash
$ cd doc
$ make clean && make html
```

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

The `Digester` includes a couple of other submodules:

#### Gullet
The `Gullet` provides a general means of downloading remote files. In
the case of the digester, it downloads the latest Wikipedia dumps. It is
capable of resuming downloads if the server supports it.

#### Adipose
The `Adipose` provides an common interface to a data-persistence store, i.e. a
database. In its current implementation, this database is MongoDB. It's
purpose is to provide some flexibility with the database. That is, a
different database could be swapped in while keeping the Adipose
interface the same.


