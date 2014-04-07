Argos
===============

![Argos](https://raw.github.com/wiki/publicscience/argos/img/argos.png)

# 0 to Argos

*Note: Most of the information here pertains to setting up an
environment for developing Argos. For deploying Argos to other
environments, such as staging or production, please refer to
[argos.cloud](https://github.com/publicscience/argos.cloud), which is
designed specifically for that purpose.*

The setup process for Argos is fairly complex, but some scripts vastly simplify it.

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

You will also need to setup the databases, which you can do with:
```bash
$ ./run db:create
```
This creates a Postgres user, `argos_user`, and sets up development and
testing databases (`argos_dev`, and `argos_test`) respectively. (If you ran `./setup` already, this step should not be necessary.)

You can optionally setup the default sources for collecting
articles by doing (make sure Postgres is running):
```bash
(venv) $ python manage.py create:sources
```

### Running & Development
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

*Note: The following commands (those with `(venv)`) assume you are in
your virtual environment. As a reminder, you can activate it like so:*
```bash
$ source /path/to/my/venv/bin/activate
```

You can setup seed data to work with:
```bash
(venv) $ python manage.py seed
```

And then run the API server:
```bash
(venv) $ python manage.py server
```

You can run the frontend ('front') server instead:
```bash
(venv) $ python front.py
```

If you make changes to the data model, make sure you create a migration:
```bash
(venv) $ python manage.py db migrate
```

And then run the migration:
```bash
(venv) $ python manage.py db upgrade
```

### Tests, Performance, Evaluation
When you get everything setup it's worth running the tests to ensure
that things have installed correctly:
```bash
(venv) $ ./run test
```

You can also profile some of the more intensive parts to identify
bottlenecks:
```bash
(venv) $ python manage.py profile
```
*Note: don't run this in production as it modifies your database.*

You can also evaluate the quality of some of the algorithms, such as
clustering:
```bash
(venv) $ python manage.py evaluate
```
*Note: don't run this in production as it modifies your database.*

*Note: If you are having import errors or the packages seem to be
missing, fear not ~ it may be because some package failed to install and
pip rolled back the installs of everything else. Check your pip logs at
`~/.pip/pip.log`. I'd wager it is `scipy` which ran into a missing
dependency.*

