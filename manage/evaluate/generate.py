"""
Generates evaluation data by filtering down
collected articles by keywords.
"""

import json
from os import path

from manage import load_articles

from argos.core.brain import tokenize
from argos.util.progress import progress_bar

def generate(keywords, num=5000):
    this_dir = path.dirname(__file__)
    articles = load_articles()

    # Filter down to articles from the specified sources.
    results = []
    articles = articles[:num]
    for idx, article in enumerate(articles):
        article_words = tokenize(article['text'])
        if set(article_words).issuperset(set(keywords)):
            results.append(article)
        progress_bar(idx/len(articles) * 100)

    # Store articles into separate text files.
    for article in results:
        #print(json.dumps(article, sort_keys=True, indent=4))
        article_path = 'unorganized_articles/{0}.txt'.format(article['title'])
        f = open(path.join(this_dir, article_path), 'wb')
        f.write(article['text'].encode('utf-8'))
