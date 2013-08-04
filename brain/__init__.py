"""
Brain
==============

Provides text processing
and "intelligence" faculties.
"""

from nltk.tokenize import sent_tokenize, word_tokenize
from nltk import FreqDist
from nltk.stem.wordnet import WordNetLemmatizer

class Brain:
    """
    Provides text processing
    and "intelligence" faculties.
    """

    def __init__(self):
        """
        Create a new brain.
        """
        pass

    def count(self, text):
        """
        Tokenize, stem, and then
        count the word frequency
        distribution of a document.

        Lemmatizing may be too slow, perhaps
        Porter Stemming should be used as a faster,
        albeit less accurate, alternative?

        Args:
            | text (str)    -- the text to process.

        Returns:
            | FreqDist      -- NLTK FreqDist object.
        """

        freqs = FreqDist()
        lemmr = WordNetLemmatizer()

        # Tokenize
        for sentence in sent_tokenize(text):
            for word in word_tokenize(sentence):

                # Lemmatize
                lemma = lemmr.lemmatize(word.lower())

                # Count
                freqs.inc(lemma)

        return freqs
