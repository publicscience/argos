"""
Brain
==============

Provides text processing
and "intelligence" faculties.
"""

# Python 2.7 support.
import sys
if sys.version_info <= (3,0):
    # Point to Py2.7 NLTK data.
    import nltk, os
    nltk.data.path = [os.path.abspath('mapreduce/nltk_data/')]

# Python 2.7 support.
try:
    from html.parser import HTMLParser
except ImportError:
    from HTMLParser import HTMLParser

from sklearn.feature_extraction.text import HashingVectorizer, TfidfVectorizer
from sklearn.decomposition import TruncatedSVD
from sklearn.cluster import DBSCAN
from nltk.tokenize import sent_tokenize, word_tokenize
from nltk.stem.wordnet import WordNetLemmatizer
from nltk.corpus import stopwords
import ner
import string

# For prototyping/experimentation purposes,
# using the AlchemyAPI
from brain import alchemy


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


class Tokenizer():
    """
    Custom tokenizer for vectorization.
    Uses Lemmatization.
    """
    def __init__(self):
        self.lemmr = WordNetLemmatizer()
    def __call__(self, doc):
        return tokenize(doc, lemmr=self.lemmr)


def vectorize(docs):
    """
    Vectorizes a list of documents.

    Args:
        | docs (list)       -- the documents to vectorize.

    Returns:
        | scipy sparse matrix (CSR/Compressed Sparse Row format)
    """
    h = HashingVectorizer(input='content', stop_words='english', norm=None, tokenizer=Tokenizer())
    return h.transform(docs)


def cluster(docs):
    """
    Clusters a list of documents.
    """
    t = TfidfVectorizer(input='content', stop_words='english', tokenizer=Tokenizer())
    lsa = TruncatedSVD(n_components=100)
    db = DBSCAN(eps=0.3, min_samples=10)

    vecs = t.fit_transform(docs)
    #vecs = lsa.fit_transform(vecs)
    results = db.fit(vecs)


def concepts(docs):
    """
    Extracts concepts for a list of documents.
    """
    return [alchemy.concepts(doc) for doc in docs]


def entities(doc):
    """
    Named entity recognition on
    a text document.

    Requires that a Stanford NER server is
    running on localhost:8080.

    Args:
        | doc (str)     -- the document to process.

    Returns:
        | set           -- set of unique entity names.
    """

    tagger = ner.SocketNER(host='localhost', port=8080)
    entities = tagger.get_entities(doc)

    # We're only interested in the entity names,
    # not their tags.
    print(entities)
    names = [entities[key] for key in entities]

    # Flatten the list of lists, return only unique values.
    return list({name for sublist in names for name in sublist})



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
    try:
        replace_punctuation = str.maketrans(string.punctuation, ' '*len(string.punctuation))
        return text.translate(replace_punctuation)

    # Python 2.7 support.
    except AttributeError:
        replace_punctuation = string.maketrans(string.punctuation, ' '*len(string.punctuation))
        rmap = dict((ord(char), u' ') for char in string.punctuation)
        if isinstance(text, str):
            text = unicode(text, 'utf-8')
        return text.translate(rmap)


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
