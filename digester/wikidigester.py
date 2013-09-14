"""
WikiDigester
==============

Handles Wikipedia dump processing.
"""

from . import Digester
from adipose import Adipose
import brain

# Goodies
from os.path import exists
from math import log
from collections import Counter
from itertools import chain

# MediaWiki parsing.
from mwlib import parser
from mwlib.refine.compat import parse_txt

# Asynchronous distributed task queue.
from celery.contrib.methods import task_method
from celery import chord, Task
from cluster.tasks import celery, workers, notify

# Serializing lxml Elements.
from lxml.etree import tostring, fromstring

# Logging.
from logger import logger
logger = logger(__name__)


NAMESPACE = 'http://www.mediawiki.org/xml/export-0.8/'
DATABASE = 'wikidigester'


class WikiDigester(Digester):
    """
    Processes Wikipedia XML pages-articles dumps.
    Subclass of Digester.
    """

    def __init__(self, file, namespace=NAMESPACE, db=DATABASE, url=None):
        """
        Initialize the WikiDigester with a file and a namespace.

        Args:
            | file (str)        -- path to XML file (or bzipped XML) to digest.
            | namespace (str)   -- namespace of the file. Defaults to MediaWiki namespace.
            | db (str)          -- the name of the database to save to.
            | url (str)         -- the url from where the dump can be fetched.
        """

        # Python 2.7 support.
        try:
            super().__init__(file, namespace)
        except TypeError:
            Digester.__init__(self, file, namespace)

        self.database = db
        self._db = None
        self.url = url

        # Keep track of number of docs.
        # Necessary for performing TF-IDF processing.
        self.num_docs = 0


    def fetch_dump(self):
        """
        Downloads this instance's Wikipedia dump to replace
        this instance's current file.
        """

        # Default dump files.
        base = 'http://dumps.wikimedia.org/enwiki/latest/'
        pages = 'enwiki-latest-pages-articles.xml.bz2'

        # Build a default url if one is not specified.
        if not self.url:
            self.url = '%s%s' % (base, pages)

        # Download!
        logger.info('Fetching pages dump from %s' % (self.url))
        self.download(self.url)


    def digest(self):
        """
        Will process this instance's dump.
        """

        # Check if the specified file exists.
        if not exists(self.file):
            logger.info('Specified file %s not found, fetching...' % self.file)
            self.fetch_dump()

        logger.info('Beginning digestion of pages.')

        # Serially/synchronously process pages.
        docs = [self._handle_page(page) for page in self._parse_pages()]

        # Generate TF-IDF representation
        # of all docs upon completion.
        self._generate_tfidf(docs)


    def _prepare_tfidf(self, docs):
        """
        Generate the corpus and pull out the
        doc ids for TF-IDF generation.

        Args:
            | docs (list)       -- a list of docs, where each doc is a tuple of
                                   ( id, [document vector] ).
                                   The "document vector" is a list of the token_ids that
                                   appeared in that document.
                                   e.g. the doc with id 12, which looked like '1 2 4 2 3 4'
                                   would be (12, [1,2,3,4])
        """
        # Separate out the titles and the document vectors.
        # e.g (12, 13, 14) and ([1,2,3], [1,3,4], [1,2,4])
        doc_ids, doc_vecs = zip(*docs)

        # To calculate how many documents each token_id appeared in,
        # first merge all the token_id-presence doc vectors into a token_id-presence corpus.
        # This is basically a mega list that is a merging of all the individual docs-as-token-lists.
        # e.g. [1,1,1,2,2,3,3,4,4]
        corpus = list(chain.from_iterable(doc_vecs))

        # Then, count all the token_ids in the corpus.
        # corpus_counts[token_id] will give the number of documents token_id appears in.
        # e.g. {1: 3, 2: 2, 3: 2, 4: 2}
        corpus_counts = dict(Counter(corpus))

        return doc_ids, corpus_counts


    def _generate_tfidf(self, docs):
        """
        Generate the TF-IDF representations for all the digested docs.

        Args:
            | docs (list)       -- see `_prepare_tfidf`.
        """
        logger.info('Page processing complete. Generating TF-IDF representations.')

        db = self.db()
        doc_ids, corpus_counts = self._prepare_tfidf(docs)

        # Iterate over all docs
        # the specified docs.
        for doc_id in doc_ids:
            doc = db.find({'_id': doc_id})
            self._calculate_tfidf(doc, corpus_counts)

        db.close()
        logger.info('TF-IDF calculations completed!')


    def _calculate_tfidf(self, doc, corpus_counts):
        """
        General TF-IDF formula:
            j_w[i] = j[i] * log_2(num_docs_corpus / num_docs_term)
        Or, more verbosely:
            tfidf weight of term i in doc j = freq of term i in doc j * log_2(num of docs in corpus/how many docs term i appears in)
        """
        db = self.db()
        tfidf_dict = {}

        # Convert each token's count to its tf-idf value.
        for token_id, token_count in doc['freqs']:
            tfidf_dict[token_id] = token_count * log((self.num_docs/corpus_counts[token_id]), 2)

        # Update the record's `doc` value to the tf-idf representation.
        # Need to convert to a list of tuples,
        # since the db won't take a dict.
        tfidf_doc = list(tfidf_dict.items())
        db.update({'_id': doc['_id']}, {'$set': {'doc': tfidf_doc }})

        db.close()

        return tfidf_doc


    def _parse_pages(self):
        """
        Parses out and yields pages from the dump.
        Only yields pages that are in
        namespace=0 (i.e. articles).
        """
        for elem in self.iterate('page'):
            # Check the namespace,
            # only namespace 0 are articles.
            # https://en.wikipedia.org/wiki/Wikipedia:Namespace
            ns = int(self._find(elem, 'ns').text)
            if ns == 0:
                self.num_docs += 1
                yield elem

        logger.info('There are %s docs in this dump.' % self.num_docs)


    def _process_page(self, elem):
        """
        Gather frequency distribution of a page,
        category names, and linked page names.
        """

        # Get the text we need.
        id          = int(self._find(elem, 'id').text)
        title       = self._find(elem, 'title').text
        datetime    = self._find(elem, 'revision', 'timestamp').text
        text        = self._find(elem, 'revision', 'text').text
        redirect    = self._find(elem, 'redirect')

        # `title` should be the canonical title, i.e. the 'official'
        # title of a page. If the page redirects to another (the canonical
        # page), the <redirect> elem contains the canonical title to which
        # the page redirects.
        if redirect is not None:
            title = redirect.attrib.get('title')

        # Extract certain elements.
        # pagelinks is a list of linked page titles.
        # categories is a list of this page's category titles.
        result = parse_txt(text)
        pagelinks = [pagelink.full_target for pagelink in result.find(parser.ArticleLink)]

        # Have to trim the beginning of Category links.
        # So 'Category:Anarchism' becomes just 'Anarchism'.
        cstart = len('Category:')
        categories = [category.full_target[cstart:] for category in result.find(parser.CategoryLink)]

        # Build the bag of words representation of the document.
        clean_text = self._clean(text)
        bag_of_words = brain.bag_of_words(clean_text)

        # Convert the bag of words to a 'sparse vector' representation.
        # Not a true sparse vector – it's really a list of (token_id, count) tuples,
        # but this works for now.
        # I'd prefer to keep it as dict, but integers as keys is invalid BSON,
        # so MongoDB rejects it.
        # When this is retrieved, it should be converted back into a dict:
        #   dict(sparse_bag_of_words)
        sparse_bag_of_words = list(bag_of_words.items())

        # Assemble the doc.
        doc = {
                'title': title,
                'datetime': datetime,
                'freqs': sparse_bag_of_words,
                'categories': categories,
                'pagelinks': pagelinks,

                # Will eventually hold the tf-idf representation.
                'doc': {}
        }

        return id, doc, bag_of_words


    def _handle_page(self, elem):
        """
        Processes then saves a page to db.
        """
        id, doc, bag_of_words = self._process_page(elem)

        # Save the doc
        # If it exists, update the existing doc.
        # If not, create it.
        self.db().update({'_id': id}, {'$set': doc})

        # Return the token_ids that were in this document.
        # Used for construction of the global doc counts for terms.
        # Need to tag it with the its doc id; this way we know
        # which page records to update.
        return ( id, list(bag_of_words.keys()) )


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


    def db(self):
        """
        Returns an interface for this digester's database.

        This will "cache" the db client so that there aren't too many.
        """
        if self._db is None:
            self._db = Adipose(self.database, 'pages')
        return self._db


    def purge(self):
        """
        Empties out the database for
        for this dump.
        """
        self.db().empty()




class WikiDigesterDistributed(WikiDigester):
    """
    A distributed version of WikiDigester.

    Distributed digestion uses Celery to asynchronously distribute the processing of the pages.

    See the WikiDigester methods for more comprehensive commenting and documentation.
    """

    def __init__(self, *args, silent=False, **kwargs):
        """
        See WikiDigester for all the args.

        Args:
            | silent (bool)        -- whether or not to send an email on digestion completion.
        """

        # Python 2.7 support.
        try:
            super().__init__(*args, **kwargs)
        except TypeError:
            WikiDigester.__init__(self, *args, **kwargs)

        self.silent = silent


    def digest(self):
        """
        Will process this instance's dump as a distributed,
        asynchronous set of tasks.
        """

        # Check if the specified file exists.
        if not exists(self.file):
            logger.info('Specified file %s not found, fetching...' % self.file)
            self.fetch_dump()

        logger.info('Beginning distributed digestion of pages.')

        # Check to see that there are workers available for distributed tasks.
        if not workers():
            logger.error('Can\'t start distributed digestion, no workers available or MQ server is not available.')
            return

        # Create async Celery tasks to
        # process pages in parallel.
        # ===
        # The tasks are in a chord, so that
        # after all tasks have been completed,
        # generate TF-IDF representation of all docs.
        # ===
        # `_generate_tfidf` has to have `self` manually
        # passed, and is a bit weird. See its definition below.
        logger.info('Creating jobs for the pages...')
        tasks = chord(self._handle_page.s(doc_id)
                      for doc_id in self._parse_pages())(self._generate_tfidf.s(self, ))


    def _parse_pages(self):
        """
        Instead of yielding the elements,
        yield the doc ids so they can fetched
        from the db.
        """
        db = self.db()
        for elem in self.iterate('page'):
            # Check the namespace,
            # only namespace 0 are articles.
            # https://en.wikipedia.org/wiki/Wikipedia:Namespace
            ns = int(self._find(elem, 'ns').text)
            if ns == 0:
                self.num_docs += 1

                # Save the raw doc (the xml) to db so that workers
                # will have access to it.
                doc_id = int(self._find(elem, 'id').text)

                doc = { 'raw': tostring(elem) }
                db.update({'_id': doc_id}, {'$set': doc})

                yield doc_id

        db.close()
        logger.info('There are %s docs in this dump.' % self.num_docs)


    @celery.task(filter=task_method)
    def _handle_page(self, doc_id):
        """
        Celery task for asynchronously handling and processing a page.

        Takes a doc_id instead of an element (elem), since we don't
        want to be passing full elements as part of the messages.
        """
        db = self.db()
        # Get the element from the cached db in the Celery task.
        doc = db.find({'_id': doc_id})
        elem = doc['raw'].decode('utf-8')

        id, doc, bag_of_words = self._process_page(fromstring(elem))

        print(doc)

        # Save/update the processed doc.
        # This is using the cached db again.
        db.update({'_id': id}, {'$set': doc})

        db.close()

        # Return this for each page, so we can build the corpus.
        return ( id, list(bag_of_words.keys()) )


    @celery.task(filter=task_method)
    def _generate_tfidf(docs, self):
        """
        The positional argument ordering here is weird,
        with `self` coming last, because of the way
        Celery passes parameters to a class method subtask.
        The *first* argument is the results of the chord's task group,
        and any arguments you pass in manually come *afterwards*.
        """
        logger.info('Page processing complete. Generating TF-IDF representations.')

        db = self.db()
        doc_ids, corpus_counts = self._prepare_tfidf(docs)

        for doc_id in doc_ids:
            # Get the doc from the cached db in the Celery task.
            doc = db.find({'_id': doc_id})
            self._calculate_tfidf(doc, corpus_counts)

        db.close()

        # Notify of completion!
        if not self.silent:
            processed_name = self.url if self.url else self.file
            notify('TF-IDF calculations complete for %s!' % processed_name)


    def db(self):
        """
        Returns an interface for this digester's database.
        """
        return Adipose(self.database, 'pages')
