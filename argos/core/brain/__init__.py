"""
Brain
==============

Provides text processing
and "intelligence" faculties.
"""

import string
from html.parser import HTMLParser

from nltk.tokenize import sent_tokenize

def sentences(doc):
    """
    Extracts sentences from a document.
    """
    return sent_tokenize(doc)

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
