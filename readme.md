Shallow Thought
===============

### Setup
Make sure to setup & activate the virtualenv before you start:
```bash
$ virtualenv shallowthought-env --no-site-packages
$ source shallowthought-env/bin/activate
```

Then you can install the dependencies:
```bash
$ pip install -r requirements.txt
```

### Testing
To run the tests:
```bash
$ nosetests
```

### MongoDB
To setup and run MongoDB ([download](http://www.mongodb.org/downloads)):
```bash
$ cd /path/to/mongodb/download
$ ./bin/mongod
```
That will run MongoDB locally at port `27107`.

### Documentation
Documentation is located at `doc/_build/html/index.html`.

To generate documentation, do:
```bash
$ cd doc
$ make clean && make html
```
