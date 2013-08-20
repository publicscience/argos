#!/bin/bash

if [[ $1 == 'doc' ]]
then
    # Build documentation.
    cd doc
    make clean
    make html

elif [[ $1 == 'mongo' ]]
then
    # Start MongoDB server.
    ./mongodb/bin/mongod --dbpath mongodb/data

elif [[ $1 == 'test' ]]
then
    # Run tests
    source dev-env/bin/activate
    nosetests

elif [[ $1 == 'profile' ]]
then
    # Profile
    source dev-env/bin/activate
    python -m cProfile -s tottime tests/wikidigester_test.py

elif [[ $1 == 'setup' ]]
then
    if [[ $2 == 'nltk' ]]
    then
        source dev-env/bin/activate
        # Install NLTK data.

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

    elif [[ $2 == 'mongo' ]]
    then
        # Setup MongoDB.
        curl -o mongodb.tgz 'http://fastdl.mongodb.org/osx/mongodb-osx-x86_64-2.4.5.tgz'
        mkdir mongodb
        tar --extract --file=mongodb.tgz --strip-components=1 --directory=mongodb
        rm mongodb.tgz
        mkdir mongodb/data

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

