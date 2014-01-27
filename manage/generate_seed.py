"""
Filter down collected articles to a a couple specific domains.
"""

import json
from os import path

base_path = path.expanduser('~/Desktop/')
this_dir = path.dirname(__file__)
dump = open(path.join(base_path,'articles.json'), 'r')
articles = json.load(dump)

# Load seed sources.
srcs = json.load(open(path.join(this_dir, 'seed/seed_sources.json'), 'r'))

# Filter down to articles from the specified sources.
filtered = [a for a in articles if a['source'] in srcs]

# Grab the last 200 articles.
a = filtered[:200]

# Dump the results to another json.
new_dump = open(path.join(this_dir, 'seed/seed.json'), 'w')
json.dump(a, new_dump)

# Store articles into separate text files.
#for article in a:
    ##print(json.dumps(article, sort_keys=True, indent=4))
    #article_path = 'articles/{0}.txt'.format(article['title'])
    #f = open(path.join(base_path, article_path), 'wb')
    #f.write(article['text'].encode('utf-8'))
