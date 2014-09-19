"""
Conceptor
==============

Concept extraction from text.
"""

import json
from urllib import request, error
from urllib.parse import urlencode

import ner
from sklearn.feature_extraction.text import HashingVectorizer

from argos.conf import APP
from . import strip
from .vectorizer import Tokenizer

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


def vectorize(concepts):
    """
    This vectorizes a list or a string of concepts;
    the regular `vectorize` method is meant to vectorize text documents;
    it is trained for that kind of data and thus is inappropriate for concepts.
    So instead we just use a simple hashing vectorizer.
    """
    h = HashingVectorizer(input='content', stop_words='english', norm='l1', tokenizer=Tokenizer())
    if type(concepts) is str:
        # Extract and return the vector for the single document.
        return h.transform([concepts]).toarray()[0]
    else:
        return h.transform(concepts)
