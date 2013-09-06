#!/bin/bash

# These are various shortcuts for commonly-used commands.
# Usage: ./do <command>

function setup_dependencies {
    # Check if OSX.
    if [[ "$OSTYPE" =~ ^darwin ]]
    then
        brew install screen
        brew install rabbitmq
        brew install wget

        # Required by mwlib.
        brew install libevent
        brew install re2c

        # MongoDB
        brew install mongodb

    # Otherwise, assume Linux...
    else 
        sudo apt-get install screen -y
        sudo apt-get install rabbitmq-server -y
        sudo apt-get install unzip -y

        # Required by mwlib.
        sudo apt-get install libevent-dev -y
        sudo apt-get install re2c -y

        # Required by lxml.
        sudo apt-get install libxml2-dev libxslt1-dev python-dev lib32z1-dev -y

        # MongoDB
        sudo apt-get install mongodb -y
    fi
}

function setup_virtualenv {
    # Setup the Python 3.3 virtualenv.
    virtualenv-3.3 dev-env --no-site-packages
    source dev-env/bin/activate
    pip install -r requirements.txt
}

function setup_nltk {
    # Download NLTK (Python 3) data.
    source dev-env/bin/activate

    # Tokenizing and lemmatization.
    python -m nltk.downloader punkt
    python -m nltk.downloader wordnet
    python -m nltk.downloader stopwords

    # Named Entity Recognition
    python -m nltk.downloader words
    # Not yet Python 3 ready:
    #python -m nltk.downloader maxent_treebank_pos_tagger
    #python -m nltk.downloader maxent_ne_chunker

    # Installing Python 3 ready alternative data.
    mkdir ~/nltk_data/chunkers
    wget -O ~/nltk_data/chunkers/maxent_ne_chunker.zip 'https://github.com/jskda/nltk_data/raw/gh-pages-repickle/packages/chunkers/maxent_ne_chunker.zip'
    unzip -o ~/nltk_data/chunkers/maxent_ne_chunker.zip -d ~/nltk_data/chunkers
    rm ~/nltk_data/chunkers/maxent_ne_chunker.zip
    mkdir ~/nltk_data/taggers
    wget -O ~/nltk_data/taggers/maxent_treebank_pos_tagger.zip 'https://github.com/jskda/nltk_data/raw/gh-pages-repickle/packages/taggers/maxent_treebank_pos_tagger.zip'
    unzip -o ~/nltk_data/taggers/maxent_treebank_pos_tagger.zip -d ~/nltk_data/taggers
    rm ~/nltk_data/taggers/maxent_treebank_pos_tagger.zip
}

function setup_mapreduce {
    # Setup the mapreduce virtualenv.
    # The mapreduce scripts require Python 2.7.
    virtualenv-2.7 mr-env --no-site-packages
    source mr-env/bin/activate
    pip install -r mapreduce/requirements.txt

    # The NTLK data then needs to be the Python 2.7 data,
    # so it will be installed to a separate directory.
    for PACKAGE in punkt wordnet stopwords words maxent_treebank_pos_tagger maxent_ne_chunker
    do
        python -m nltk.downloader $PACKAGE -d mapreduce/nltk_data/
    done
}

function setup_doc {
    source dev-env/bin/activate
    cd doc
    make clean
    make html
}


# Build documentation.
if [[ $1 == 'doc' ]]
then
    setup_doc


# Start MongoDB server.
elif [[ $1 == 'mongo' ]]
then
    mongod --dbpath db


# Run tests.
elif [[ $1 == 'test' ]]
then
    source dev-env/bin/activate
    nosetests


# Run profiler.
elif [[ $1 == 'profile' ]]
then
    source dev-env/bin/activate
    python profiler.py


# Start a local Celery worker.
elif [[ $1 == 'worker' ]]
then
    src_dir=`dirname $0`
    cd $src_dir
    source dev-env/bin/activate
    celery worker --loglevel=info --config=cluster.celery_config


elif [[ $1 == 'digest' ]]
then
    source dev-env/bin/activate
    python digest.py


# Start RabbitMQ server.
elif [[ $1 == 'mq' ]]
then
    rabbitmq-server


# Start screen session with everything setup.
elif [[ $1 == 'go' ]]
then
    screen -S shallowthought -c .screen


# Setup some stuff.
elif [[ $1 == 'setup' ]]
then

    # Set up a new development
    # or master environment.
    if [[ $2 == 'all' ]]
    then
        setup_dependencies
        setup_virtualenv
        setup_nltk
        setup_doc

    # Set up a minion/worker environment.
    elif [[ $2 == 'worker' ]]
    then
        setup_dependencies
        setup_virtualenv
        setup_nltk

    elif [[ $2 == 'deps' ]]
    then
        setup_dependencies

    elif [[ $2 == 'venv' ]]
    then
        setup_virtualenv

    elif [[ $2 == 'nltk' ]]
    then
        setup_nltk

    elif [[ $2 == 'mapreduce' ]]
    then
        setup_mapreduce

    fi
fi
