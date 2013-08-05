"""
Text
==============

Text processing utilities.
"""

from html.parser import HTMLParser
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
    replace_punctuation = str.maketrans(string.punctuation, ' '*len(string.punctuation))
    return text.translate(replace_punctuation)

def sanitize(html):
    """
    Strips HTML markup.
    """
    s = Sanitizer()
    s.feed(html)
    return s.get_data()

class Sanitizer(HTMLParser):
    def __init__(self):
        super().__init__(strict=False)
        self.reset()
        self.fed = []
    def handle_data(self, d):
        self.fed.append(d)
    def get_data(self):
        return ''.join(self.fed)
