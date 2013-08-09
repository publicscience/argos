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
DATABASE = 'shallowthought'

class WikiDigester(Digester):
    """
    Processes Wikipedia XML dumps.
    Subclass of Digester.
    """

    def __init__(self, file, dump, namespace=NAMESPACE):
        """
        Initialize the WikiDigester with a file and a namespace.
        The dumps can be:
            * abstract => abstracts
            * pagelinks => links between pages
            * pages => i.e. pages-articles, the actual content

        Args:
            | file (str)        -- path to XML file (or bzipped XML) to digest.
            | dump (str)        -- the name of the dump ('abstract', 'pagelinks', 'pages')
            | namespace (str)   -- namespace of the file. Defaults to MediaWiki namespace.
        """
        super().__init__(file, namespace)
        self.dump = dump
        self.brain = Brain()

        # Create db interface.
        self.db = Adipose(DATABASE, self.dump)


    def fetch_dump(self):
        """
        Downloads this instance's Wikipedia dump to replace
        this instance's current file.
        """

        dumps = {
                    'base': 'http://dumps.wikimedia.org/enwiki/latest/',
                    'abstract': 'enwiki-latest-abstract.xml',
                    'pagelinks': 'enwiki-latest-pagelinks.sql.gz',
                    'pages': 'enwiki-latest-pages-articles.xml.bz2'
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

        if self.dump == 'pages':
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
        a = Adipose(DATABASE, self.dump)
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

        # Get the text we need.
        id = elem.find('{%s}id' % NAMESPACE).text
        title = elem.find('{%s}title' % NAMESPACE).text
        datetime = elem.find('{%s}timestamp' % NAMESPACE).text
        text = elem.find('{%s}revision' % NAMESPACE).find('{%s}text' % NAMESPACE).text
        text = self._clean(text)

        # Get freq dist data.
        data = dict(self.brain.count(text))

        # Assemble the doc.
        doc = {
                '_id': id,
                'title': title,
                'datetime': datetime,
                'freqs': data
              }

        # Save the doc
        self.db.update({'_id': id}, doc)
