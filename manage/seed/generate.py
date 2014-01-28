"""
Generates seed data by filtering down
collected articles to a few specific sources.
"""

import json
from os import path
from manage import load_articles

def generate(num=200):
    articles = load_articles()

    # Load seed sources.
    srcs = json.load(open(path.join(this_dir, 'seed_sources.json'), 'r'))

    # Filter down to articles from the specified sources.
    filtered = [a for a in articles if a['source'] in srcs]

    # Grab the maximum articles from the top.
    a = filtered[:num]

    # Dump the results to another json.
    new_dump = open(path.join(this_dir, 'seed.json'), 'w')
    json.dump(a, new_dump)
