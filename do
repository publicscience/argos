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

        # Redis
        brew install redis

        # Bzr, for python-dateutil
        brew install bzr

        # gfortran, for building scipy
        brew install gfortran

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

        # Redis
        sudo apt-get install redis -y

        # Bzr, for python-dateutil
        sudo apt-get install bzr -y
    fi
}

function setup_virtualenv {
    # Setup the Python 3.3 virtualenv.
    virtualenv-3.3 dev-env --no-site-packages
    source dev-env/bin/activate
    pip install numpy
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

function setup_ner {
    wget -O ner.zip 'http://nlp.stanford.edu/software/stanford-ner-2013-06-20.zip'
    unzip -o ner.zip
    mv 'stanford-ner-2013-06-20' ner
    rm ner.zip
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


# Start the Stanford NER server.
elif [[ $1 == 'ner' ]]
then
    cd ner
    java -mx1000m -cp stanford-ner.jar edu.stanford.nlp.ie.NERServer -loadClassifier classifiers/english.conll.4class.distsim.crf.ser.gz -port 8080 -outputFormat inlineXML


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


# Start RabbitMQ server.
elif [[ $1 == 'mq' ]]
then
    rabbitmq-server

# Start redis server.
elif [[ $1 == 'redis' ]]
then
    redis-server


# Start screen session with everything setup.
elif [[ $1 == 'go' ]]
then
    screen -S development -c .screen


elif [[ $1 == 'nltk' ]]
then
    setup_nltk


# Setup some stuff.
elif [[ $1 == 'setup' ]]
then
    setup_dependencies
    setup_virtualenv
    setup_ner
    setup_nltk
    setup_doc
fi
