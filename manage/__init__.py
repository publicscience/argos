import json
from os import path

from argos.datastore import db

def load_articles():
    base_path = path.expanduser('../')
    this_dir = path.dirname(__file__)
    dump = open(path.join(base_path,'articles.json'), 'r')
    return json.load(dump)
