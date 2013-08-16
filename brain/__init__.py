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

from nltk.tokenize import sent_tokenize, word_tokenize
from nltk import FreqDist
from nltk.stem.wordnet import WordNetLemmatizer
from nltk.corpus import stopwords
from nltk.tag import pos_tag
from nltk.chunk import batch_ne_chunk
import string

class Brain:
    """
    Provides text processing
    and "intelligence" faculties.
    """

    def __init__(self):
        """
        Create a new brain.
        """

    def count(self, text, threshold=0):
        """
        Tokenize, stem, and then
        count the word frequency
        distribution of a document.

        Lemmatizing may be too slow, perhaps
        Porter Stemming should be used as a faster,
        albeit less accurate, alternative?

        Args:
            | text (str)        -- the text to process.
            | threshold (int)   -- optionally return only words
                                with a count above this threshold.

        Returns:
            | FreqDist      -- NLTK FreqDist object.
        """

        freqs = FreqDist()
        lemmr = WordNetLemmatizer()
        stops = list(string.punctuation) + stopwords.words('english')

        # Tokenize
        for sentence in sent_tokenize(text):
            for word in word_tokenize(sentence):

                # Ignore punctuation and stopwords
                if word in stops:
                    continue

                # Lemmatize
                lemma = lemmr.lemmatize(word.lower())

                # Count
                freqs.inc(lemma)

        # Filter frequencies
        if threshold:
            freqs = {word: count for word, count in freqs.items() if count > threshold}

        return freqs

    def recognize(self, text):
        """
        Named entity recognition on
        some text.

        Args:
            | text (str)    -- the text to process.

        Returns:
            | set           -- set of unique entity names.
        """

        sents     = sent_tokenize(text)
        tokenized = [word_tokenize(sent) for sent in sents]
        tagged    = [pos_tag(sent) for sent in tokenized]
        chunked   = batch_ne_chunk(tagged, binary=True)

        entities = []
        for tree in chunked:
            entities.extend(self._extract_entities(tree))

        return set(entities)

    def _extract_entities(self, tree):
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
                    entities.extend(self._extract_entities(child))
        return entities
