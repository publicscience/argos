"""
Adipose
==============

Provides an interface to a database.
Uses MongoDB, but can be modified.
"""

import pymongo
import config

class Adipose:
    """
    Provides an interface to a database (MongoDB).
    """
    def __init__(self, database, collection, host=config.DB_HOST, port=27017):
        """
        Create a new interface.

        Args:
            | database (str)    -- The name of the database to connect to.
            | collection (str)  -- The name of the collection or table to use.
            | host (str)        -- The database host.
            | port (int)        -- The port number of the host.

        Example::

            adipose = Adipose('wikipedia', 'vectors')
        """

        # Connect to Mongo
        self.client = pymongo.MongoClient(host, port)

        # Select a database
        self.db = self.client[database]

        # Select a collection
        self.collection = self.db[collection]


    def add(self, data):
        """
        Add data to the db.

        Args:
            | data (dict) -- the data to be saved.
            | data (list) -- list of dicts to be saved.

        Example::

            adipose.add({'title': 'foo', 'category': 'fum'})
        """
        self.collection.insert(data)


    def update(self, query, data):
        """
        Updates or creates a new record.

        Args:
            | query (dict) -- query to locate record to update.
            | data (dict)  -- updated data.

        Example::

            adipose.update({'title': 'foo'}, {'category': 'bar'})
        """
        self.collection.update(query, data, upsert=True)


    def index(self, key):
        """
        Indexes the data by the specified key.

        Args:
            | key (str) -- key to index on
        """
        self.collection.ensure_index('title', unique=True)


    def find(self, query):
        """
        Searches db for a record matching
        the query.

        Args:
            | query (dict) -- the query to be searched.

        Returns:
            | dict -- the result of the query.
        """
        return self.collection.find_one(query)


    def all(self):
        """
        Returns an iterable for all records
        in the collection.

        Example::

            for doc in adipose.all():
                # do stuff

        Returns:
            | iterable -- cursor to iterate over all docs with.
        """
        return self.collection.find()


    def empty(self):
        """
        Empties the database collection/table.
        """
        self.collection.remove()


    def count(self):
        """
        Returns number of docs/records in collection/table.

        Returns:
            | int -- number of docs/records in the collection/table.
        """
        return self.collection.count()

