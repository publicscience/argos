"""
Article
==============

Article objects.
"""

from brain import vectorize, entities

class Article:
    def __init__(self):
        pass

    def load(self):
        pass

    def save(self):
        pass

    def vectorize(self):
        # Articles are represented by:
        # – bag of words vector
        # – entities vector
        if not hasattr(self, 'vectors'):
            bow_vec = vectorize(self.text)
            ent_vec = vectorize(' '.join(entities(self.text)))
            self.vectors = [bow_vec, ent_vec]
        return self.vectors
