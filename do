#!/bin/bash

# These are various shortcuts for commonly-used commands.
# Usage: ./do <command>


# Build documentation.
if [[ $1 == 'doc' ]]
then
    cd doc
    make clean
    make html


# Start MongoDB server.
elif [[ $1 == 'mongo' ]]
then
    ./mongodb/bin/mongod --dbpath mongodb/data


# Run tests.
elif [[ $1 == 'test' ]]
then
    source dev-env/bin/activate
    nosetests


# Run profiler.
elif [[ $1 == 'profile' ]]
then
    source dev-env/bin/activate
    python -m cProfile -s tottime tests/wikidigester_test.py


# Start a local Celery worker.
elif [[ $1 == 'worker' ]]
then
    source dev-env/bin/activate
    celery worker --loglevel=info --config=tasks.config


# Start RabbitMQ server.
elif [[ $1 == 'mq' ]]
then
    rabbitmq-server


# Start screen session with everything setup.
elif [[ $1 == 'go' ]]
then
    screen -S shallowthought -c .screen


# Startup Vim in the proper env.
elif [[ $1 == 'dev' ]]
then
    source dev-env/bin/activate
    vim .


# Setup some stuff.
elif [[ $1 == 'setup' ]]
then

    # Install NLTK data (Python 3)
    if [[ $2 == 'nltk' ]]
    then
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

        # Installing Python 3 ready alternative data
        curl -o ~/nltk_data/chunkers/maxent_ne_chunker.zip 'https://github.com/jskda/nltk_data/blob/gh-pages-repickle/packages/chunkers/maxent_ne_chunker.zip'
        unzip ~/nltk_data/chunkers/maxent_ne_chunker.zip
        curl -o ~/nltk_data/taggers/maxent_treebank_pos_tagger.zip 'https://github.com/jskda/nltk_data/blob/gh-pages-repickle/packages/taggers/maxent_treebank_pos_tagger.zip'
        unzip ~/nltk_data/taggers/maxent_treebank_pos_tagger.zip


    # Install MongoDB
    elif [[ $2 == 'mongo' ]]
    then
        # Setup MongoDB.
        curl -o mongodb.tgz 'http://fastdl.mongodb.org/osx/mongodb-osx-x86_64-2.4.5.tgz'
        mkdir mongodb
        tar --extract --file=mongodb.tgz --strip-components=1 --directory=mongodb
        rm mongodb.tgz
        mkdir mongodb/data

    # Setup MapReduce NLTK packages (Python 2.7)
    elif [[ $2 == 'mapreduce' ]]
    then
        source mr-env/bin/activate
        # The mapreduce scripts require Python 2.7.
        # The NTLK data then needs to be the Python 2.7 data,
        # so it will be installed to a separate directory.
        for PACKAGE in punkt wordnet stopwords words maxent_treebank_pos_tagger maxent_ne_chunker
        do
            python -m nltk.downloader $PACKAGE -d mapreduce/nltk_data/
        done
    fi
fi

