"""
Text
==============

Text processing utilities.
"""

from HTMLParser import HTMLParser

def trim(text):
    """
    Compresses and trims extra whitespace.
    """
    return ' '.join(text.split())

def sanitize(html):
    """
    Strips HTML markup.
    """
    s = Sanitizer()
    s.feed(html)
    return s.get_data()

class Sanitizer(HTMLParser):
    def __init__(self):
        self.reset()
        self.fed = []
    def handle_data(self, d):
        self.fed.append(d)
    def get_data(self):
        return ''.join(self.fed)
