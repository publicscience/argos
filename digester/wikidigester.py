"""
WikiDigester
==============

Handles Wikipedia dump processing.
"""

from . import Digester
from adipose import Adipose
import brain

from mwlib import parser
from mwlib.refine.compat import parse_txt

from tasks import celery

from lxml.etree import tostring, fromstring

NAMESPACE = 'http://www.mediawiki.org/xml/export-0.8/'
DATABASE = 'shallowthought'

class WikiDigester(Digester):
    """
    Processes Wikipedia XML dumps.
    Subclass of Digester.
    """

    def __init__(self, file, dump, namespace=NAMESPACE, distrib=False):
        """
        Initialize the WikiDigester with a file and a namespace.
        The dumps can be:
            * pages => i.e. pages-articles, the actual content

        Args:
            | file (str)        -- path to XML file (or bzipped XML) to digest.
            | dump (str)        -- the name of the dump ('pages')
            | namespace (str)   -- namespace of the file. Defaults to MediaWiki namespace.
            | distrib (bool)    -- whether or not digestion should be distributed. Default to False.

        Distributed digestion uses Celery to asynchronously distribute the processing of the pages.
        """

        # Python 2.7 support.
        try:
            super().__init__(file, namespace)
        except TypeError:
            Digester.__init__(self, file, namespace)

        self.dump = dump
        self.distrib = distrib


    def fetch_dump(self):
        """
        Downloads this instance's Wikipedia dump to replace
        this instance's current file.
        """

        dumps = {
                    'base': 'http://dumps.wikimedia.org/enwiki/latest/',
                    'pages': 'enwiki-latest-pages-articles.xml.bz2'
                }

        # Build full url.
        url = '%s%s' % (dumps['base'], dumps[self.dump])

        # Download!
        self.download(url)


    def purge(self):
        """
        Empties out the database for
        for this dump.
        """
        self._db().empty()


    def digest(self):
        """
        Will process this instance's dump.
        Each kind of dump is processed differently.
        """

        if self.dump == 'pages':
            self.iterate('page', self._process_pages)


    def _process_pages(self, elem):
        """
        Processes pages that are in
        namespace=0 (i.e. articles).
        """

        # Check the namespace,
        # only namespace 0 are articles.
        # https://en.wikipedia.org/wiki/Wikipedia:Namespace
        ns = int(self._find(elem, 'ns').text)
        if ns != 0: return

        # Process the page.
        if self.distrib:
            # Send the processing of this page as
            # an async task to a worker.
            self._process_page_task.delay(tostring(elem))
        else:
            # Process synchronously.
            self._process_page(elem)


    def _process_page(self, elem):
        """
        Gather frequency distribution of a page,
        category names, and linked page names,
        and store to the database.
        """

        # Get the text we need.
        id          = int(self._find(elem, 'id').text)
        title       = self._find(elem, 'title').text
        datetime    = self._find(elem, 'revision', 'timestamp').text
        text        = self._find(elem, 'revision', 'text').text
        redirect    = self._find(elem, 'redirect')

        # 'ctitle' indicates 'canonical title', i.e. the redirect title, which appears
        # to be the 'official' title of a page. Not all pages have redirects.
        # Redirects are the title that alternative titles redirect *to*,
        # thus they could be considered canonical.
        if redirect is not None:
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
        data = dict(brain.count(clean_text, threshold=2))

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
        self._db().update({'_id': id}, {'$set': doc})


    from celery.contrib.methods import task_method
    @celery.task(filter=task_method)
    def _process_page_task(self, elem):
        """
        Celery task for asynchronously processing a page.
        """
        self._process_page(fromstring(elem))


    def _find(self, elem, *tags):
        """
        Finds a particular subelement of an element.

        Args:
            | elem (lxml Element)  -- the MediaWiki text to cleanup.
            | *tags (strs)      -- the tag names to use. See below for clarification.

        Returns:
            | lxml Element -- the target element.

        You need to provide the tags that lead to it.
        For example, the `text` element is contained
        in the `revision` element, so this method would
        be used like so::

            self._find(elem, 'revision', 'text')

        This method is meant to replace chaining calls
        like this::

            text_el = elem.find('{%s}revision' % NAMESPACE).find('{%s}text' % NAMESPACE)
        """
        for tag in tags:
            elem = elem.find('{%s}%s' % (NAMESPACE, tag))
        return elem


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
        return brain.depunctuate(text)


    def _db(self):
        """
        Returns an interface for this digester's database.

        If a database interface has been set externally,
        just return that one.

        Otherwise, return the 'canonical' database for this digester.

        This approach is used instead of saving a database interface as
        as instance variable because the latter approach encounters issues
        when using distributed tasks.

        The database interface cannot be properly serialized for distributed tasks,
        so instead we just create a new interface when we need it.
        """
        if hasattr(self, 'db'):
            return self.db
        else:
            return Adipose(DATABASE, self.dump)
