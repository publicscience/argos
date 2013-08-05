"""
WikiDigester
==============

Handles Wikipedia dump processing.
"""

import string
from digester import Digester
from adipose import Adipose
from brain import Brain
from mwlib import parser
from mwlib.refine.compat import parse_txt

NAMESPACE = 'http://www.mediawiki.org/xml/export-0.8/'

class WikiDigester(Digester):
    """
    Processes Wikipedia XML dumps.
    Subclass of Digester.
    """

    def __init__(self, file, dump, namespace=NAMESPACE):
        """
        Initialize the WikiDigester with a file and a namespace.

        Args:
            | file (str)        -- path to XML file (or bzipped XML) to digest.
            | dump (str)        -- the name of the dump ('abstract', 'pagelinks', 'pages-articles')
            | namespace (str)   -- namespace of the file. Defaults to MediaWiki namespace.
        """
        super().__init__()
        self.dump = dump


    def fetch_dump(self):
        """
        Downloads this instance's Wikipedia dump to replace
        this instance's current file.
        """

        dumps = {
                    'base': 'http://dumps.wikimedia.org/enwiki/latest/',
                    'abstract': 'enwiki-latest-abstract.xml',
                    'pagelinks': 'enwiki-latest-pagelinks.sql.gz',
                    'pages-articles': 'enwiki-latest-pages-articles.xml.bz2'
                }

        # Build full url.
        url = '%s%s' % (dumps['base'], dumps[self.dump])

        # Download!
        self.download(url)


    def digest(self):
        """
        Will process this instance's dump.
        Each kind of dump is processed differently.
        """

        if self.dump == 'pages-articles':
            d.iterate('page', self._process_pages)
        elif self.dump == 'pagelinks':
            pass
        elif self.dump == 'abstract':
            pass


    def _clean(self, text):
        """
        Cleans up MediaWiki text of markup.
        Currently a 'naive' version in that
        it just strips *all* punctuation.

        Will eventually want to strip out unnecessary
        markup syntax as well, such as "File:" and
        "Category".

        Args:
            | text (str)    -- the MediaWiki text to cleanup. Must be utf-8 encoded.

        Returns:
            | str -- the replaced text.
        """

        # Strip all punctuation.
        replace_punctuation = string.maketrans(string.punctuation, ' '*len(string.punctuation))
        return text.translate(replace_punctuation)


    def _process_pages(self, elem):
        #a = Adipose('test', 'pages')
        text = elem.find('{%s}revision' % NAMESPACE).find('{%s}text' % NAMESPACE).text.encode('utf-8')

        #a.empty() #for testing
        #a.add(data)
