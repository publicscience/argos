import unittest

from argos.core.brain import summarize

class SummarizeTest(unittest.TestCase):

    def test_summarize(self):
        doc = open('tests/data/multidoc/1.txt', 'r').read()
        summary = summarize.summarize('Why the Middle Class Is Declining', doc, summary_length=5)
        summary_without_nones = list(filter(None, summary))
        self.assertEqual(len(summary_without_nones), 5)

    def test_multidoc_summarize(self):
        docs = [open('tests/data/multidoc/{0}.txt'.format(i+1), 'r').read() for i in range(4)]
        summary = summarize.multisummarize(docs, summary_length=5)
        summary_without_nones = list(filter(None, summary))
        self.assertEqual(len(summary_without_nones), 5)
