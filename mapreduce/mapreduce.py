#!../mr-env/bin/python

"""
MapReduce
==============

MapReduce jobs for use with mrjob.

Currently not being used, but being reserved
for later usage (I imagine it will come in handy
when doing more text processing?)
"""

from mrjob.job import MRJob
from nltk.tokenize import sent_tokenize, word_tokenize
from nltk.stem.wordnet import WordNetLemmatizer
from nltk.corpus import stopwords
import string

class MRWordFreqCount(MRJob):
    def mapper_init(self):
        self.lemmr = WordNetLemmatizer()
        self.stops = list(string.punctuation) + stopwords.words('english')

    def mapper(self, key, line):
        # Tokenize
        for sentence in sent_tokenize(line):
            for word in word_tokenize(sentence):
                # Skip stopwords
                if word in self.stops:
                    continue

                # Lemmatize
                lemma = self.lemmr.lemmatize(word.lower())
                yield (lemma, 1)

    def combiner(self, word, counts):
        yield (word, sum(counts))

    def reducer(self, word, counts):
        yield (word, sum(counts))

if __name__ == '__main__':
     MRWordFreqCount.run()
