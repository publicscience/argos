'''
Adipose
==============

Stores data to db.
Uses MongoDB, but can be modified.
'''

import pymongo

class Adipose:
    def __init__(self, database, collection, host='localhost', port=27017):
        '''
        Example:
            adipose = Adipose('wikipedia', 'vectors')
        '''
        # Connect to Mongo
        self.client = pymongo.MongoClient(host, port)

        # Select a database
        self.db = self.client[database]

        # Select a collection
        self.collection = self.db[collection]

    def add(self, data):
        '''
        Add data to the db.
        data (dict) -- the data to be saved.
        data (list) -- list of dicts to be saved.

        Example:
            adipose.add({'title': 'foo', 'category': 'fum'})
        '''
        self.collection.insert(data)

    def update(self, query, data):
        '''
        Updates or creates a new record.
        query (dict) -- query to locate record to update
        data (dict)  -- updated data

        Example:
            adipose.update({'title': 'foo'}, {'category': 'bar'})
        '''
        self.collection.update(query, data, upsert=True)

    def index(self, key):
        '''
        Indexes the data by title.
        key (str) -- key to index on
        '''
        self.collection.ensure_index('title', unique=True)

    def find(self, query):
        '''
        Searches db for a record matching
        the query.
        query (dict) -- the query to be searched.
        '''
        return self.collection.find_one(query)

    '''
        Note: will want to keep track of metadata too, such as
        when the database was last updated.
    '''

