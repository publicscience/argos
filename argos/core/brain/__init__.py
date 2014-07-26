"""
Brain
==============

Provides text processing
and "intelligence" faculties.
"""

import json
import string
from collections import Counter
from urllib import request, error
from urllib.parse import urlencode
from html.parser import HTMLParser

import ner

from argos.conf import APP

from argos.util.logger import logger
logger = logger(__name__)

def concepts(docs, strategy='stanford'):
    """
    Named entity recognition on
    a text document or documents.

    Requires that a Stanford NER server or a DBpedia Spotlight
    server is running at argos.conf.APP['KNOWLEDGE_HOST'],
    depending on which strategy you choose.

    Args:
        | docs (list)       -- the documents to process.
        | doc (str)         -- the document to process.
        | strategy (str)    -- the strategy to use, default is `stanford`. can be `stanford` or `spotlight`.

    Returns:
        | list              -- list of all entity mentions
    """
    if type(docs) is str:
        docs = [docs]

    entities = []

    if strategy == 'stanford':
        tagger = ner.SocketNER(host=APP['KNOWLEDGE_HOST'], port=8080)

        for doc in docs:
            try:
                ents = tagger.get_entities(doc)
            except UnicodeDecodeError as e:
                logger.exception('Unexpected unicode decoding error: {0}'.format(e))
                ents = {}

            # We're only interested in the entity names,
            # not their tags.
            names = [ents[key] for key in ents]

            # Flatten the list of lists.
            names = [strip(name) for sublist in names for name in sublist]

            entities += names

        # TEMPORARILY REMOVED, THIS PART IS HANDLED EXTERNALLY BY A VECTORIZER.
        # Calculate (rough, naive) normalized weights for the entities.
        # Will likely want to find ways to recognize congruent entities which
        # may not necessarily be consistently mentioned, i.e. "Bill Clinton" and "Clinton" (not yet implemented).
        #counts = Counter(entities)
        #if len(counts):
            #top_count = counts.most_common(1)[0][1]
        #results = []
        #for entity, count in counts.items():
            #results.append((entity, count/top_count))
        #return results

    elif strategy == 'spotlight':
        '''
        Example response from DBpedia Spotlight:
        {
          "@text": "Brazilian state-run giant oil company Petrobras signed a three-year technology and research cooperation agreement with oil service provider Halliburton.",
          "@confidence": "0.0",
          "@support": "0",
          "@types": "",
          "@sparql": "",
          "@policy": "whitelist",
          "Resources":   [
                {
              "@URI": "http://dbpedia.org/resource/Brazil",
              "@support": "74040",
              "@types": "Schema:Place,DBpedia:Place,DBpedia:PopulatedPlace,Schema:Country,DBpedia:Country",
              "@surfaceForm": "Brazilian",
              "@offset": "0",
              "@similarityScore": "0.9999203720889515",
              "@percentageOfSecondRank": "7.564391175472872E-5"
            },
                {
              "@URI": "http://dbpedia.org/resource/Petrobras",
              "@support": "387",
              "@types": "DBpedia:Agent,Schema:Organization,DBpedia:Organisation,DBpedia:Company",
              "@surfaceForm": "Petrobras",
              "@offset": "38",
              "@similarityScore": "1.0",
              "@percentageOfSecondRank": "0.0"
            },
                {
              "@URI": "http://dbpedia.org/resource/Halliburton",
              "@support": "458",
              "@types": "DBpedia:Agent,Schema:Organization,DBpedia:Organisation,DBpedia:Company",
              "@surfaceForm": "Halliburton",
              "@offset": "140",
              "@similarityScore": "1.0",
              "@percentageOfSecondRank": "0.0"
            }
          ]
        }

        As you can see, it provides more (useful) data than we are taking advantage of.
        '''
        endpoint = 'http://{host}:2222/rest/annotate'.format(host=APP['KNOWLEDGE_HOST'])
        for doc in docs:
            data = {
                    'text': doc,
                    'confidence': 0,
                    'support': 0
                   }
            url = '{endpoint}?{data}'.format(endpoint=endpoint, data=urlencode(data))
            req = request.Request(url,
                    headers={
                        'Accept': 'application/json'
                    })
            try:
                res = request.urlopen(req)
            except error.HTTPError as e:
                logger.exception('Error extracting entities (strategy=spotlight) with doc: {0}\n\nError: {1}'.format(doc, e.read()))
                raise e
            if res.status != 200:
                raise Exception('Response error, status was not 200')
            else:
                content = res.read()
                entities = json.loads(content.decode('utf-8'))['Resources']
                return [entity['@surfaceForm'] for entity in entities]

    else:
        raise Exception('Unknown strategy specified. Please use either `stanford` or `spotlight`.')

    return entities


def trim(text):
    """
    Compresses and trims extra whitespace.
    """
    return ' '.join(text.split())


def depunctuate(text):
    """
    Removes all punctuation from text,
    replacing them with spaces.
    """
    punctuation = string.punctuation + '“”‘’–"'
    try:
        replace_punctuation = str.maketrans(punctuation, ' '*len(punctuation))
        return text.translate(replace_punctuation)

    # Python 2.7 support.
    except AttributeError:
        replace_punctuation = string.maketrans(punctuation, ' '*len(punctuation))
        rmap = dict((ord(char), u' ') for char in punctuation)
        if isinstance(text, str):
            text = unicode(text, 'utf-8')
        return text.translate(rmap)

def strip(text):
    """
    Removes punctuation from the beginning
    and end of text.
    """
    punctuation = string.punctuation + '“”‘’–"'
    return text.strip(punctuation)

def sanitize(html):
    """
    Strips HTML markup.
    """
    s = Sanitizer()
    s.feed(html)
    return s.get_data()


class Sanitizer(HTMLParser):
    def __init__(self):
        # Python 2.7 support.
        try:
            super().__init__(strict=False)
        except TypeError:
            HTMLParser.__init__(self)

        self.reset()
        self.fed = []
    def handle_data(self, d):
        self.fed.append(d)
    def get_data(self):
        return ''.join(self.fed)
