"""
Brain
==============

Provides text processing
and "intelligence" faculties.
"""

import string

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
    replace_punctuation = str.maketrans(punctuation, ' '*len(punctuation))
    return text.translate(replace_punctuation)

def strip(text):
    """
    Removes punctuation from the beginning
    and end of text.
    """
    punctuation = string.punctuation + '“”‘’–"'
    return text.strip(punctuation)
