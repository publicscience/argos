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


    def add(self, doc):
        """
        Add doc to the db.
        If bulk inserting (i.e. passing in a list),
        will automatically break the list into smaller lists if it exceeds Mongo's maximum message size.

        Args:
            | doc (dict) -- the doc to be saved.
            | doc (list) -- list of docs to be saved.

        Example::

            adipose.add({'title': 'foo', 'category': 'fum'})
        """

        # Check size of message, if bulk inserting.
        if isinstance(doc, list) and sys.getsizeof(doc) > MAX_MESSAGE_SIZE:
            # If there's only one doc and it's still too large,
            # then the doc is just too large.
            if len(doc) == 1:
                raise InvalidDocument('Document exceeds maximum message size (%s)' % MAX_MESSAGE_SIZE)

            # If it is too large, recursively split in half until each message is an appropriate size.
            midpoint = int(len(doc)/2)
            self.add(doc[:midpoint])
            self.add(doc[midpoint:])
        else:
            self.collection.insert(doc)


    def update(self, query, data):
        """
        Updates or creates a new record.
        This is different than `save` in that you query the record,
        and then pass in only the data you want to update (not the entire doc).

        An example use case is if you want to only change part
        of a doc, rather than get the whole thing.

        Args:
            | query (dict) -- query to locate record to update.
            | data (dict)  -- updated data (optional)

        Example::

            adipose.update({'title': 'foo'}, {'category': 'bar'})
        """
        self.collection.update(query, {'$set': data}, upsert=True)


    def save(self, doc):
        """
        Saves or creates a new record.
        This is different than `update` in that you pass in
        an entire document, rather than a query and a partial document.

        An example use case is if you fetch an entire record,
        then manipulate it locally, and want to save the entire thing.

        Args:
            | doc (dict)  -- the doc to save.

        Returns:
            | id of saved document

        Example::

            adipose.save({'title': 'foo', 'category': 'bar'})
        """
        return self.collection.save(doc)


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


    def all(self, query=None):
        """
        Returns an iterable for all records,
        or all records for a query,
        in the collection.

        Args:
            | query (dict) -- the query to be searched. Optional, defaults to None, which returns ALL records.

        Example::

            for doc in adipose.all():
                # do stuff

        Returns:
            | iterable -- cursor to iterate over all docs with.
        """
        if query:
            return self.collection.find(query)
        else:
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

