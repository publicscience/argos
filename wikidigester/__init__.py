"""
WikiDigester
==============

Handles Wikipedia dump processing.
"""

from digester import Digester
from adipose import Adipose
from textutils import depunctuate
from brain import Brain

from mwlib import parser
from mwlib.refine.compat import parse_txt

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
            * pages => i.e. pages-articles, the actual content

        Args:
            | file (str)        -- path to XML file (or bzipped XML) to digest.
            | dump (str)        -- the name of the dump ('pages')
            | namespace (str)   -- namespace of the file. Defaults to MediaWiki namespace.
        """
        super().__init__(file, namespace)
        self.dump = dump
        self.brain = Brain()

        # Create db interface.
        self.db = Adipose(DATABASE, self.dump)


    def fetch_dump(self):
        """
        Downloads this instance"s Wikipedia dump to replace
        this instance"s current file.
        """

        dumps = {
                    'base': 'http://dumps.wikimedia.org/enwiki/latest/',
                    'pages': 'enwiki-latest-pages-articles.xml.bz2'
                }

        # Build full url.
        url = '%s%s' % (dumps['base'], dumps[self.dump])

        # Download!
        self.download(url)


    def digest(self):
        """
        Will process this instance"s dump.
        Each kind of dump is processed differently.
        """

        if self.dump == 'pages':
            self.iterate('page', self._process_pages)


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
        Currently a "naive" version in that
        it just strips *all* punctuation.

        Will eventually want to strip out unnecessary
        markup syntax as well, such as 'File:' and
        'Category'.

        Args:
            | text (str)    -- the MediaWiki text to cleanup.

        Returns:
            | str -- the replaced text.
        """
        return depunctuate(text)


    def _process_pages(self, elem):
        """
        Gather frequency distribution of a page,
        category names, and linked page names,
        and store to the database.
        """

        # Get the text we need.
        id = int(elem.find('{%s}id' % NAMESPACE).text)
        title = elem.find('{%s}title' % NAMESPACE).text
        datetime = elem.find('{%s}revision' % NAMESPACE).find('{%s}timestamp' % NAMESPACE).text
        text = elem.find('{%s}revision' % NAMESPACE).find('{%s}text' % NAMESPACE).text
        redirect = elem.find('{%s}redirect' % NAMESPACE)

        # 'ctitle' indicates 'canonical title', i.e. the redirect title, which appears
        # to be the 'official' title of a page. Not all pages have redirects.
        # Redirects are the title that alternative titles redirect *to*,
        # thus they could be considered canonical.
        if redirect:
            ctitle = redirect.attrib.get('title')
        else:
            ctitle = title

        # Extract certain elements.
        # pagelinks is a list of linked page titles.
        # categories is a list of this page's category titles.
        result = parse_txt(text)
        pagelinks = [pagelink.full_target for pagelink in result.find(parser.ArticleLink)]

        # Have to trim the beginning of Category links.
        # So 'Category:Anarchism' becomes just 'Anarchism'.
        cstart = len('Category:')
        categories = [category.full_target[cstart:] for category in result.find(parser.CategoryLink)]

        # Get freq dist data.
        clean_text = self._clean(text)
        data = dict(self.brain.count(clean_text))

        # Assemble the doc.
        doc = {
                'title': title,
                'redirect': ctitle,
                'datetime': datetime,
                'freqs': data,
                'categories': categories,
                'pagelinks': pagelinks
              }

        # Save the doc
        # If it exists, update the existing doc.
        # If not, create it.
        self.db.update({'_id': id}, {'$set': doc})
