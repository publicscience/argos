"""
Dictionary
==============

A hash dictionary, which maps token_ids->tokens
using the hashing trick.

That is, a token_id is formed for a word by passing
that word through a hashing function.

The default hashing function is zlib.adler32.

There is potential for hash collisions, but it is very
unlikely. In corpuses large enough where it's a bit
more likely to happen, the collision will more than likely
be inconsequential (i.e. the collision of two infrequent tokens).

Because this dictionary uses the hashing trick, it can be
used 'online', i.e. documents can be computed on-the-fly
without needing to see the whole corpus first.

Derived from gensim 0.8.6's HashDictionary,
copyright (C) 2012 Homer Strong, Radim Rehurek.

Licensed under the GNU LGPL v2.1.
http://www.gnu.org/licenses/lgpl.html
"""

import zlib
import itertools
from collections import Counter

class Dictionary():
    """
    A (hash) dictionary.
    """

    def __init__(self, documents=None, id_limit=10000, hash_func=zlib.adler32, debug=False):
        """
        Initialize the Dictionary with a hash function
        and a maximum amount of token ids.

        Args:
            | id_limit (int)    -- the maximum amount of token ids this dictionary can hold.
            | hash_func (func)  -- the hashing function to use for generating token ids.
        """
        self.hash_func = hash_func
        self.id_limit = id_limit
        self.debug = debug

        # Keep track of number of documents,
        # number of positions (i.e. total number of tokens, including repeats),
        # and number of nonzero tokens (i.e. tokens encountered at least once).
        self.num_docs, self.num_positions, self.num_nonzero = 0, 0, 0

        # Keep track of token frequencies.
        # Only updated if debug=True.
        self.freqs = {}

        # If documents have been specified,
        # add them to the Dictionary.
        if documents:
            self.add_docs(documents)


    def _hash(self, token):
        """
        Hashes a token (i.e. generates a token's id).

        Args:
            | token (str)       -- the token to hash.

        Returns:
            | int               -- the token's hash.
        """
        return self.hash_func( token.encode('utf-8') ) % self.id_limit


    def doc_to_bag_of_words(self, doc):
        """
        Convert a document to a bag-of-words representation,
        i.e. a list of (token_id, token_count).

        Args:
            | doc (str)         -- the document to convert.

        Returns:
            | list              -- list of (token_id, token_count)
                                   for the document.
        """

        # Convert document to a sorted list,
        # so that identical tokens are grouped together.
        doc = sorted(doc)

        # Dict to store results in,
        # mapping token_id->token_count
        results = {}

        # Iterate over the tokens in the document,
        # grouping identical tokens.
        for token, group in itertools.groupby(doc):

            # Get frequency of this word in the document.
            freq = len(list(group))

            # Generate the token's id.
            token_id = self._hash(token)

            # Update this token's frequency.
            results[token_id] = results.get(token_id, 0) + freq

        # Update the statistics of the Dictionary.
        self.num_docs += 1
        self.num_positions += len(doc)
        self.num_nonzero += len(results)

        # Update the freq counts for the whole dictionary,
        # by merging the existing freqs with this new set of results.
        if self.debug:
            self.freqs = dict(Counter(self.freqs) + Counter(results))

        # Return results in ascending id order.
        return sorted(results.items())



    def add_docs(self, docs):
        """
        Add documents to this Dictionary.,
        converting each one to a bag-of-words.

        Args:
            | docs (iter)       -- an iterable yielding documents to add.
        """
        for doc_num, doc in enumerate(docs):
            self.doc_to_bag_of_words(doc)


    def filter_tokens(self, min=5, max=0.5, keep=None):
        """
        Filters out tokens not meeting the specified
        document-appearance criteria.

        Args:
            | min (int)     -- the minimum amount of docs the token must appear in.
                               Tokens appearing in less than this many docs will be removed 
            | max (float)   -- the maximum *fraction* of total corpus size allowed
                               for a token. Tokens appearing in more than this many docs
                               will be removed.
            | keep (int)    -- the amount of tokens to keep after filtering. Keeps all if keep=None.

        Note: might not need this.
        """
        pass


    def __len__(self):
        """
        See how many unique tokens are in the dictionary.

        Returns:
            | int               -- the number of unique token ids in the dictionary.
        """
        return self.id_limit


    def keys(self):
        """
        See all the token ids in the dictionary.

        Returns:
            | list              -- list of all the dictionary's token ids.
        """
        return range(len(self))
