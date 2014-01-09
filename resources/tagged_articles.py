import json

dump = open('articles.json', 'rb')
articles = json.load(dump)

tagged = [article for article in articles if article['tags']]
