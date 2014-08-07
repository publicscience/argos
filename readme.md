Argos
===============

![Argos](https://raw.github.com/wiki/publicscience/argos/img/argos.png)

# 0 to Argos

*Note: Most of the information here pertains to setting up an
environment for developing Argos. For deploying Argos to other
environments, such as staging or production, please refer to
[argos.cloud](https://github.com/publicscience/argos.cloud), which is
designed specifically for that purpose.*

*Note: Argos requires some training data, which can be collected using
the [argos.corpora](https://github.com/publicscience/argos.corpora) project.
This project also can collect testing/evaluation data for assessing the
quality of Argos' clustering.*

* [Setup](#setup)
    * [Dependencies](#dependencies)
    * [Database](#database)
    * [Training](#training-the-vectorizer)
* [Running & Development](#running--development)
    * [Migrations](#changes-to-the-data-model-migrations)
* [Testing](#testing)
* [Performance](#performance)
* [Evaluation](#evaluation)
* [Deployment](#deployment)
* [Guide to the project](#guide-to-the-project)
* [Notes](#notescaveatsmiscellany)

---

## Setup
The setup process for Argos is fairly complex, but some scripts vastly simplify it.

*Note on virtualenvs: Many of the following commands (those preceded by `(argos)`) assume you are in your virtual environment. As a reminder, you can activate it like so:*
```bash
# by default, the setup script creates a virtualenv at ~/env/argos
$ source ~/env/argos/bin/activate
```

### Dependencies
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
download and setup [Stanford NER](http://nlp.stanford.edu/software/CRF-NER.shtml#Download), 
download and setup [Apache Jena](https://jena.apache.org) & [Fuseki](https://jena.apache.org/documentation/serving_data/index.html),
and generate the documentation.

### Database
You will also need to setup the databases, which you can do with:
```bash
$ ./run db:create
```
This creates a Postgres user, `argos_user`, and sets up development and
testing databases (`argos_dev`, and `argos_test`) respectively. (If you ran `./setup` already, this step should not be necessary.)

You can optionally setup the default sources for collecting
articles by doing (make sure Postgres is running):
```bash
(argos) $ python manage.py create:sources
```

### Training the Vectorizer
Finally, you will need to train the vectorizer pipeline for the brain,
which is implemented in `argos.core.brain.vectorizer`. You can train this
pipeline with a JSON file of training data structured like so:
```
[
    {
        'title': 'Some title',
        'text': 'Some text'
    }, {
        'title': 'Another article',
        'text': 'Foo bar'
    },
    ...
]
```

And then the training is accomplished like so:
```bash
(argos) $ python manage.py train /path/to/training/data.json
```

This will serialize (pickle) the trained pipeline to the `PIPELINE_PATH`
specified in the config. This pipeline is used specifically to vectorize
*news articles* so that should probably be what your training data is
composed of. You can collect this data using
[argos.corpora](https://github.com/publicscience/argos.corpora).

---

## Running & Development
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
* Apache Jena Fuseki (3030)
* A Celery worker

*Note: If you're running this on Ubuntu, some of these processes may
fail, but it is because they are already running as services. Don't
worry about it.*

Then when you're done, kill it with:
```bash
$ kill <pid>
```


You can setup seed data to work with:
```bash
(argos) $ python manage.py seed
```

And then run the API server:
```bash
(argos) $ python manage.py server
```

You can run the frontend ('front') server instead:
```bash
(argos) $ python front.py
```

To add a user as an admin:
```bash
(argos) $ python manage.py create:admin someone@someplace.com
```

### Changes to the data model (Migrations)
If you make changes to the data model, make sure you create a migration:
```bash
(argos) $ python manage.py db migrate
```

And then run the migration:
```bash
(argos) $ python manage.py db upgrade
```

If you run into errors like:
```
sqlalchemy.exc.ProgrammingError: (ProgrammingError) column "<something>" of relation "article" already exists)
```
it's likely because your database is already fully-migrated (perhaps you
created a new one from scratch, based off the latest data model). You
just need to properly "stamp" the database with the latest revision ID so that
Alembic (which manages the migrations) knows that its up-to-date:
```bash
(argos) $ python manage.py db stamp head
```
This marks the database as at the latest (`head`) revision.

---

## Testing
When you get everything setup it's worth running the tests to ensure
that things have installed correctly:
```bash
(argos) $ ./run test
```

You can also run more specific test modules:
```bash
(argos) $ ./run test tests/core
(argos) $ ./run test tests/core/article_test.py
```

---

## Performance

You can also profile some of the more intensive parts to identify
bottlenecks:
```bash
(argos) $ python manage.py profile
```
**Note: don't run this in production as it modifies your database.**

---

## Evaluation
You can also evaluate the quality of some of the algorithms (currently
only the article=>event and event=>story clustering).

The project comes with a few datasets to use for evaluation, located in
`manage/core/evaluate/data/`. They are not particularly large,
but you can generate more evaluation datasets using
[argos.corpora](https://github.com/publicscience/argos.corpora)'s
`sampler` functionality (which will generate "pre-labeled" event
clusters by parsing WikiNews dumps).

The evaluation commands perform a grid search across different
similarity thresholds and strategies (see below for more details),
scoring the results against the pre-labeled clusters.

Note that the clustering algorithm used is a hierarchical agglomerative
one, so the main things under examination in these evaluations are:

* The quality of the similarity metric, which measures how similar two
articles or events are.
* The threshold for which the similarity metric indicates that two
articles or events are sufficiently similar to be grouped together.

To run the evaluations:
```bash
(argos) $ python manage.py evaluate:event
(argos) $ python manage.py evaluate:story
```
**Note: don't run this in production as it modifies your database.** 

These will run evaluations on the provided datasets. To pass in a
different dataset:
```bash
(argos) $ python manage.py evaluate:event -d /path/to/my/dataset.json
```

The dataset is expected to be in JSON format and adhere to a certain
structure, which is what the `argos.corpora` sampler outputs.

An HTML report will be output to `manage/core/evaluate/reports/` with some details.
You can look at the cluster members and determine for yourself if they
look right.


New similarity strategies can be patched in by defining methods in
either `manage/core/evaluate/strategies/event.py` or
`manage/core/evaluate/strategies/story.py`. The methods must have `similarity`
in their name to be registered as an alternative similarity strategy.

The only requirement is that the method's parameters are `(self, obj)`,
where obj is the object being compared to, and that it returns a float
value from `0.0` to `1.0`, where `0.0` is completely dissimilar and
`1.0` means identical.


---

## Deployment

See [argos.cloud](https://github.com/publicscience/argos.cloud).

---

## Guide to the project
Here are some quick notes to help you navigate through the project.

**argos/core** --
The core modules which provide the primary functionality of Argos.

Consists of:
* *core/brain* – summarization, clustering, entity extraction, providing
"knowledge" for concepts, etc.
* *core/digester* – processes data dumps.
* *core/membrane* – interfaces with the outside world: collects
articles, gets information about them (such as shared counts), etc.

**argos/web** --
All functionality which opens up Argos' core to the web, divided into
API and "front" (the end-user frontend) packages.

**argos/tasks** --
For distributed and regular tasks (via Celery).

---

## Notes/Caveats/Miscellany
If you are having import errors or the packages seem to be
missing, fear not ~ it may be because some package failed to install and
pip rolled back the installs of everything else. Check your pip logs at
`~/.pip/pip.log`. I'd wager it is `scipy` which ran into a missing
dependency.

