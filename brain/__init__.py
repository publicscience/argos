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

from nltk.tokenize import sent_tokenize, word_tokenize
from nltk.stem.wordnet import WordNetLemmatizer
from nltk.corpus import stopwords
from nltk.tag import pos_tag
from nltk.chunk import batch_ne_chunk
import string
import zlib

MAX_INT = 2147483647

def bag_of_words(doc, id_limit=MAX_INT, hash_func=zlib.adler32):
    """
    Tokenize, stem, and then
    count the word frequency
    distribution of a document,
    using the hashing trick,
    to build a bag of words representation
    of the document.

    Lemmatizing may be too slow, perhaps
    Porter Stemming should be used as a faster,
    albeit less accurate, alternative?

    Args:
        | doc (str)         -- the text document to process.
        | id_limit (int)    -- the maximum amount of token ids this dictionary can hold. Defaults to int32 max (2147483647), it is recommended you scale that back if you don't need that much.
        | hash_func (func)  -- the hashing function to use for generating token ids.

    Returns:
        | dict              -- the bag of words; i.e. dict of {token_id: count}
    """

    # Bag of words
    wbag = {}

    lemmr = WordNetLemmatizer()
    stops = set(list(string.punctuation) + stopwords.words('english'))

    # Tokenize
    for sentence in sent_tokenize(doc):
        for token in word_tokenize(sentence):

            # Ignore punctuation and stopwords
            if token in stops:
                continue

            # Lemmatize
            lemma = lemmr.lemmatize(token.lower())

            # Hash token into its token id.
            token_id = hash_func( token.encode('utf-8') ) % MAX_INT

            # Increment count for this token id.
            wbag[token_id] = wbag.get(token_id, 0) + 1

    return wbag


def recognize(doc):
    """
    Named entity recognition on
    a text document.

    Args:
        | doc (str)     -- the document to process.

    Returns:
        | set           -- set of unique entity names.
    """

    sents     = sent_tokenize(doc)
    tokenized = [word_tokenize(sent) for sent in sents]
    tagged    = [pos_tag(sent) for sent in tokenized]
    chunked   = batch_ne_chunk(tagged, binary=True)

    entities = []
    for tree in chunked:
        entities.extend(_extract_entities(tree))

    return set(entities)


def _extract_entities(tree):
    """
    Extract entities from a tree.

    Args:
        | tree (Tree) -- the tree to extract from.
    """
    entities = []
    if hasattr(tree, 'node') and tree.node:
        if tree.node == 'NE':
            entities.append(' '.join([child[0] for child in tree]))
        else:
            for child in tree:
                entities.extend(_extract_entities(child))
    return entities


def compare(docA, docB):
    pass


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
