"""
Corpus
==============

A corpus.

Derived from gensim 0.8.6's TextCorpus & WikiCorpus,
copyright (C) 2010 Radim Rehurek <radimrehurek@seznam.cz>,
copyright (C) 2012 Lars Buitinck <larsmans@gmail.com>.

Licensed under the GNU LGPL v2.1.
http://www.gnu.org/licenses/lgpl.html
"""

from .dictionary import Dictionary
from nltk.tokenize import word_tokenize

class Corpus():

    def __init__(self, filename, dictionary=None):
        """
        Initialize the Corpus with an input filename
        and a Dictionary.

        Args:
            | filename (str)            -- the input filename.
            | dictionary (Dictionary)   -- the Dictionary for this Corpus to use.
        """
        self.filename = filename

        if dictionary:
            self.dictionary = dictionary
        else:
            self.dictionary = Dictionary()

        # Add the documents from the input file
        # to the Dictionary.
        self.dictionary.add_docs( self.get_docs() )


    def __iter__(self):
        """
        Iterable for the corpus.

        Yields:
            | A bag-of-words representation of each document in the corpus.
        """
        for doc in self.get_docs():
            yield self.dictionary.doc_to_bag_of_words(doc)


    def get_stream(self):
        """
        Streams the Corpus's input file.

        Returns:
            | The input stream.
        """
        input = self.filename

        # If `input` is a string,
        # it's a filename.
        if isinstance(input, basestring):
            return open(input)

        # Otherwise, `input` assumed to be
        # file-like object.
        else:
            # Reset stream to beginning.
            input.seek(0)
            return input


    def get_docs(self):
        """
        Iterable that gets documents from the Corpus's
        input stream, yielding them one by one.

        Yields:
            | The tokenized line for each line in the stream.
        """

        # Keep track of how many documents
        # are in the corpus.
        self.length = 0

        # Iterate over the input file stream.
        for line_num, line in enumerate(self.get_stream()):
            self.length += 1

            # Yield each line's tokens.
            yield word_tokenize(line.lower())


    def __len__(self):
        """
        See how many documents are in the corpus.

        Returns:
            | int   -- the number of docs in the corpus.
        """
        return self.length
