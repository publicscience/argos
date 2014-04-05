"""
Generates seed data by filtering down
collected articles to a few specific sources.
"""

import json

def generate(num=50):
    dump = open('../articles.json', 'r')
    articles = json.load(dump)

    # Load seed sources.
    srcs = json.load(open('manage/data/seed_sources.json', 'r'))
    srcs_urls = [src[1] for src in srcs]

    # Filter down to articles from the specified sources.
    filtered = [a for a in articles if a['source'] in srcs_urls]

    # Grab the maximum articles from the top.
    a = filtered[:num]

    # Dump the results to another json.
    new_dump = open('manage/data/seed.json', 'w')
    json.dump(a, new_dump)
