"""
WikiDigester
==============

Handles Wikipedia dump processing.
"""

from digester import Digester
from adipose import Adipose
from textutils import depunctuate
from brain import Brain

# mwlib does not support python 3. need to look for alternatives...
#from mwlib import parser
#from mwlib.refine.compat import parse_txt

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
        super().__init__(file, namespace)
        self.dump = dump
        self.brain = Brain()


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
            self.iterate('page', self._process_pages)
        elif self.dump == 'pagelinks':
            pass
        elif self.dump == 'abstract':
            pass


    def purge(self):
        """
        Empties out the database for
        for this dump.
        """
        a = Adipose('test', 'pages')
        a.empty()


    def _clean(self, text):
        """
        Cleans up MediaWiki text of markup.
        Currently a 'naive' version in that
        it just strips *all* punctuation.

        Will eventually want to strip out unnecessary
        markup syntax as well, such as "File:" and
        "Category".

        Args:
            | text (str)    -- the MediaWiki text to cleanup.

        Returns:
            | str -- the replaced text.
        """
        return depunctuate(text)


    def _process_pages(self, elem):
        """
        Gather frequency distribution of a page,
        and store to a database.
        """

        # Create db interface.
        a = Adipose('test', 'pages')

        # Get the text we need.
        title = elem.find('{%s}title' % NAMESPACE).text
        text = elem.find('{%s}revision' % NAMESPACE).find('{%s}text' % NAMESPACE).text
        text = self._clean(text)

        # Get freq dist data.
        data = dict(self.brain.count(text))

        # Assemble the doc.
        doc = {
                'title': title,
                'freqs': data
              }

        a.empty() #for testing
        #a.add(doc)
