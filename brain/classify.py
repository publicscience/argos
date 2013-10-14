"""
Classify
==============

Provides an interface to classification,
and its training.
"""

from sklearn.naive_bayes import MultinomialNB
from brain import vectorize
import pickle

class Classifier():
    def __init__(self):
        """
        Initialize a classifier.
        """
        self.clf = MultinomialNB()


    def classify(self, docs, num_topics=5):
        """
        Classify a list of documents.

        Args:
            | docs (list)       -- the documents to classify (a list of strings)
            | num_topics (int)  -- number of top predicted topics
                                   to return for each doc.

        Returns:
            | list -- the list of lists of document topics.
        """

        # Returns a 2d array, where each array is
        # a list of probabilities for labels.
        docs_ = vectorize(docs)
        probs = self.clf.predict_proba(docs_)

        # This will sort the *indices* of the inner arrays, instead of the actual values.
        # These indices correspond with labels.
        # It goes from low to high.
        probs_sorted = probs.argsort()

        # Slice all the inner arrays to get `num_topics` top probabilities (their indices).
        probs_top = probs_sorted[:, -num_topics:]

        # Convert the indices to the actual labels, and return.
        return [self.clf.classes_[probs_indices] for prob_indices in top_probs]


    def train(self, docs, labels):
        """
        Train the classifier with documents and labels.
        The training can be online. That is, an existing
        classifier can be updated with new training data.

        Args:
            | docs (list)       -- the documents to train on (a list of strings)
            | labels (list)     -- the labels to train on (a list of lists of strings)
        """
        docs_ = vectorize(docs)
        self.clf.partial_fit(docs_, labels)
