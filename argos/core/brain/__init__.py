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
from nltk.tokenize import sent_tokenize, word_tokenize
from nltk.stem.wordnet import WordNetLemmatizer
from nltk.corpus import stopwords
import ner
import string
from collections import Counter

from argos.conf import APP

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
        | docs (str)        -- a single document to vectorize.

    Returns:
        | scipy sparse matrix (CSR/Compressed Sparse Row format)
    """
    h = HashingVectorizer(input='content', stop_words='english', norm=None, tokenizer=Tokenizer())

    if type(docs) is str:
        # Extract and return the vector for the single document.
        return h.transform([docs]).toarray()[0]
    else:
        return h.transform(docs)


def concepts(docs, strategy='stanford'):
    """
    Named entity recognition on
    a text document or documents.

    Requires that a Stanford NER server is running
    at argos.conf.APP['KNOWLEDGE_HOST'].

    Args:
        | docs (list)       -- the documents to process.
        | doc (str)         -- the document to process.
        | strategy (str)    -- the strategy to use, default is stanford.

    Returns:
        | list              -- list of all entity mentions
    """
    if type(docs) is str:
        docs = [docs]

    entities = []

    if strategy == 'stanford':
        tagger = ner.SocketNER(host=APP['KNOWLEDGE_HOST'], port=8080)

        for doc in docs:
            ents = tagger.get_entities(doc)
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

    elif strategy == 'nltk':
        names = []
        from nltk.tag import pos_tag
        from nltk.chunk import batch_ne_chunk
        for doc in docs:
            sentences = sent_tokenize(doc)
            tokenized_sentences = [word_tokenize(sent) for sent in sentences]
            tagged = [pos_tag(sent) for sent in tokenized_sentences]
            chunked = batch_ne_chunk(tagged, binary=True) # binary=False will tag entities as ORGANIZATION, etc.

            for tree in chunked:
                names.extend(_extract_entities(tree))
        entities = [strip(name) for name in names]

    else:
        raise Exception('Unknown strategy specified.')

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


def _extract_entities(tree):
    entities = []
    if hasattr(tree, 'node') and tree.node:
        if tree.node == 'NE':
            entities.append(' '.join([child[0] for child in tree]))
        else:
            for child in tree:
                entities.extend(_extract_entities(child))
    return entities
