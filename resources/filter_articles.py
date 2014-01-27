"""
Filter down collected articles to a a couple specific domains.
"""

import json

dump = open('/Users/ftseng/Desktop/articles.json', 'r')
articles = json.load(dump)

#tagged = [article for article in articles if article['tags']]

srcs = [
        'http://feeds.feedburner.com/AtlanticPoliticsChannel',
        'http://feeds.feedburner.com/AtlanticInternational',
        'http://www.nytimes.com/services/xml/rss/nyt/World.xml',
        'http://www.nytimes.com/services/xml/rss/nyt/Politics.xml',
        'http://www.nytimes.com/services/xml/rss/nyt/US.xml',
        'http://www.spiegel.de/international/world/index.rss',
        'http://www.foreignpolicy.com/node/feed',
        'http://rss.csmonitor.com/feeds/politics',
        'http://rss.csmonitor.com/feeds/world'
        'http://feeds.theguardian.com/theguardian/us/rss',
        'http://www.independent.co.uk/news/world/rss',
        'http://feeds.washingtonpost.com/rss/politics',
        'http://feeds.washingtonpost.com/rss/world',
        'http://blogs.wsj.com/capitaljournal/feed/',
        'http://online.wsj.com/xml/rss/3_7085.xml',
        'http://feeds.bbci.co.uk/news/world/rss.xml',
        'http://feeds.bbci.co.uk/news/politics/rss.xml',
        'http://www.economist.com/rss/international_rss.xml',
        'http://www.economist.com/rss/united_states_rss.xml',
        'http://feeds.reuters.com/Reuters/PoliticsNews'
]

articles_ = [a for a in articles if a['source'] in srcs]
a = articles_[:200]
for article in a:
    #print(json.dumps(article, sort_keys=True, indent=4))
    f = open('/Users/ftseng/Desktop/articles/{0}.txt'.format(article['title'], 'wb'))
    f.write(article['text'].encode('utf-8'))
