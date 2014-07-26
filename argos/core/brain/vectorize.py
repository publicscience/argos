"""
Vectorize
==============

Handles vectorizing of documents.
"""

import os, pickle
import string

from sklearn.feature_extraction.text import HashingVectorizer, TfidfTransformer, CountVectorizer
from sklearn.pipeline import Pipeline
from sklearn.decomposition import TruncatedSVD
from sklearn.preprocessing import Normalizer

from nltk.tokenize import sent_tokenize, word_tokenize
from nltk.stem.wordnet import WordNetLemmatizer
from nltk.corpus import stopwords

from argos.conf import APP

from argos.util.logger import logger
logger = logger(__name__)


class Tokenizer():
    """
    Custom tokenizer for vectorization.
    Uses Lemmatization.
    """
    def __init__(self):
        self.lemmr = WordNetLemmatizer()
    def __call__(self, doc):
        return tokenize(doc, lemmr=self.lemmr)


PIPELINE_PATH = os.path.expanduser(os.path.join(APP['PIPELINE_PATH'], 'pipeline.pickle'))
if os.path.isfile(PIPELINE_PATH):
    PIPELINE = pickle.load(open(PIPELINE_PATH, 'rb'))
else:
    PIPELINE = False

def train(docs):
    """
    Trains and serializes (pickles) a vectorizing pipeline
    based on training data.

    `min_df` is set to filter out extremely rare words,
    since we don't want those to dominate the distance metric.

    `max_df` is set to filter out extremely common words,
    since they don't convey much information.
    """
    pipeline = Pipeline([
        #('vectorizer', HashingVectorizer(input='content', stop_words='english', norm=None, lowercase=True, tokenizer=Tokenizer())),
        ('vectorizer', CountVectorizer(input='content', stop_words='english', lowercase=True, tokenizer=Tokenizer(), min_df=0.015, max_df=0.9)),
        ('tfidf', TfidfTransformer(norm=None, use_idf=True, smooth_idf=True)),
        ('feature_reducer', TruncatedSVD(n_components=100)),
        ('normalizer', Normalizer(copy=False))
    ])

    logger.info('Training on {0} docs...'.format(len(docs)))
    pipeline.fit(docs)

    PIPELINE = pipeline

    pipeline_file = open(PIPELINE_PATH, 'wb')
    pickle.dump(pipeline, pipeline_file)
    logger.info('Training complete.')

def tokenize(doc, **kwargs):
    """
    Tokenizes a document, using a lemmatizer.

    Args:
        | doc (str)                 -- the text document to process.

    Returns:
        | list                      -- the list of tokens.
    """

    tokens = []
    lemmr = kwargs.get('lemmr', WordNetLemmatizer())
    stops = set(list(string.punctuation) + stopwords.words('english'))

    # Tokenize
    for sentence in sent_tokenize(doc):
        for token in word_tokenize(sentence):

            # Ignore punctuation and stopwords
            if token in stops:
                continue

            # Lemmatize
            lemma = lemmr.lemmatize(token.lower())
            tokens.append(lemma)
    return tokens


def sentences(doc):
    """
    Extracts sentences from a document.
    """
    return sent_tokenize(doc)


def vectorize(docs):
    """
    Vectorizes a list of documents using
    a trained vectorizing pipeline.

    Args:
        | docs (list)       -- the documents to vectorize.
        | docs (str)        -- a single document to vectorize.

    Returns:
        | scipy sparse matrix (CSR/Compressed Sparse Row format)
    """
    if not PIPELINE:
        raise Exception('No pipeline is loaded. Have you trained one yet?')

    if type(docs) is str:
        # Extract and return the vector for the single document.
        return PIPELINE.transform([docs])[0]
    else:
        return PIPELINE.transform(docs)

def vectorize_concepts(concepts):
    """
    This vectorizes a list or a string of concepts;
    the regular `vectorize` method is meant to vectorize text documents;
    it is trained for that kind of data and thus is inappropriate for concepts.
    So instead we just use a simple hashing vectorizer.
    """
    h = HashingVectorizer(input='content', stop_words='english', norm=None, tokenizer=Tokenizer())
    if type(concepts) is str:
        # Extract and return the vector for the single document.
        return h.transform([concepts]).toarray()[0]
    else:
        return h.transform(concepts)
