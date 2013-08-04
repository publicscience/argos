"""
Sanitizer
==============

Strips HTML markup from text.
Thanks: http://stackoverflow.com/a/925630
"""

from HTMLParser import HTMLParser

class MLStripper(HTMLParser):
    def __init__(self):
        self.reset()
        self.fed = []
    def handle_data(self, d):
        self.fed.append(d)
    def get_data(self):
        return ''.join(self.fed)

def sanitize(html):
    s = MLStripper()
    s.feed(html)
    return s.get_data()
