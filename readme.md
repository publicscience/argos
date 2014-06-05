Argos
===============

![Argos](https://raw.github.com/wiki/publicscience/argos/img/argos.png)

# 0 to Argos

*Note: Most of the information here pertains to setting up an
environment for developing Argos. For deploying Argos to other
environments, such as staging or production, please refer to
[argos.cloud](https://github.com/publicscience/argos.cloud), which is
designed specifically for that purpose.*

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

## Testing, Performance, Evaluation
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

You can also profile some of the more intensive parts to identify
bottlenecks:
```bash
(argos) $ python manage.py profile
```
**Note: don't run this in production as it modifies your database.**

You can also evaluate the quality of some of the algorithms, such as
clustering:
```bash
(argos) $ python manage.py evaluate
```
**Note: don't run this in production as it modifies your database.**

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

