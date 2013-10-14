"""
Adipose
==============

Provides an interface to a database.
Uses MongoDB, but can be modified.
"""

import pymongo
import config
import sys
import pickle, bson
from pymongo.errors import InvalidDocument

# Maximum MongoDB message size, in bytes.
MAX_MESSAGE_SIZE = 48000000

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
        If bulk inserting (i.e. passing in a list),
        will automatically break the list into smaller lists if it exceeds Mongo's maximum message size.

        Args:
            | data (dict) -- the data to be saved.
            | data (list) -- list of dicts to be saved.

        Example::

            adipose.add({'title': 'foo', 'category': 'fum'})
        """

        # Check size of message, if bulk inserting.
        if isinstance(data, list) and sys.getsizeof(data) > MAX_MESSAGE_SIZE:
            # If there's only one doc and it's still too large,
            # then the doc is just too large.
            if len(data) == 1:
                raise InvalidDocument('Document exceeds maximum message size (%s)' % MAX_MESSAGE_SIZE)

            # If it is too large, recursively split in half until each message is an appropriate size.
            midpoint = int(len(data)/2)
            self.add(data[:midpoint])
            self.add(data[midpoint:])
        else:
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


    def remove(self, query):
        """
        Removes a record.

        Args:
            | query (dict) -- query to locate record to update.
        """
        self.collection.remove(query)


    def index(self, key='_id', enforce_uniqueness=False):
        """
        Indexes the data by the specified key.
        This enforces key uniqueness by dropping duplicates,
        if specified,
        and ignores docs without the key (i.e. is sparse).

        Args:
            | key (str) -- key to index on
        """
        self.collection.ensure_index(key, unique=True, dropDups=enforce_uniqueness, sparse=True)


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


    def close(self):
        """
        Close the connection.
        """
        self.client.close()


    def pickle(self, obj):
        """
        Helper for properly pickling/encoding for the database.
        """
        return bson.binary.Binary(pickle.dumps(obj))


    def unpickle(self, obj):
        """
        Helper for properly unpickling from the database.
        """
        return pickle.loads(obj)

