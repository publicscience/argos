import sys
import json
from os import path

from argos.datastore import db

def progress(percent):
    """
    Show a progress bar.
    """
    width = 100
    sys.stdout.write('[{0}] {1}'.format(' ' * width, '{:8.4f}'.format(percent)))
    sys.stdout.flush()
    sys.stdout.write('\b' * (width+10))

    for i in range(int(percent)):
        sys.stdout.write('=')
        sys.stdout.flush()
    sys.stdout.write('\b' * (width+10))

def load_articles():
    base_path = path.expanduser('~/Desktop/')
    this_dir = path.dirname(__file__)
    dump = open(path.join(base_path,'articles.json'), 'r')
    return json.load(dump)
