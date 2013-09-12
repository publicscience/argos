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
from celery import chord
from cluster.tasks import celery, workers, notify

# Serializing lxml Elements.
from lxml.etree import tostring, fromstring

# Logging.
from celery.utils.log import get_task_logger
from logger import logger
logger = logger(__name__)


NAMESPACE = 'http://www.mediawiki.org/xml/export-0.8/'
DATABASE = 'wikidigester'


class WikiDigester(Digester):
    """
    Processes Wikipedia XML dumps.
    Subclass of Digester.
    """

    def __init__(self, file, dump='pages', namespace=NAMESPACE, distrib=False, db=DATABASE, url=None, silent=False):
        """
        Initialize the WikiDigester with a file and a namespace.
        The dumps can be:
            * pages => i.e. pages-articles, the actual content

        Args:
            | file (str)        -- path to XML file (or bzipped XML) to digest.
            | dump (str)        -- the name of the dump ('pages')
            | namespace (str)   -- namespace of the file. Defaults to MediaWiki namespace.
            | distrib (bool)    -- whether or not digestion should be distributed. Defaults to False.
            | db (str)          -- the name of the database to save to.
            | url (str)         -- the url from where the dump can be fetched.
            | silent (bool)     -- whether or not to send email notifications.

        Distributed digestion uses Celery to asynchronously distribute the processing of the pages.
        """

        # Python 2.7 support.
        try:
            super().__init__(file, namespace)
        except TypeError:
            Digester.__init__(self, file, namespace)

        self.database = db
        self.dump = dump
        self.distrib = distrib
        self.url = url
        self.silent = silent

        # Keep track of number of docs.
        # Necessary for performing TF-IDF processing.
        self.num_docs = 0

        # Setup Celery's logger if necessary.
        if self.distrib:
            logger = get_task_logger(__name__)


    def fetch_dump(self):
        """
        Downloads this instance's Wikipedia dump to replace
        this instance's current file.
        """

        # Default dump files.
        dumps = {
                    'base': 'http://dumps.wikimedia.org/enwiki/latest/',
                    'pages': 'enwiki-latest-pages-articles.xml.bz2'
                }

        # Build a default url if one is not specified.
        if not self.url:
            self.url = '%s%s' % (dumps['base'], dumps[self.dump])

        # Download!
        logger.info('Fetching %s dump from %s' % (self.dump, self.url))
        self.download(self.url)


    def purge(self):
        """
        Empties out the database for
        for this dump.
        """
        self.db().empty()
        self.corpus().empty()


    def digest(self):
        """
        Will process this instance's dump.
        Each kind of dump is processed differently.
        """

        # Check if the specified file exists.
        if not exists(self.file):
            logger.info('Specified file %s not found, fetching...' % self.file)
            self.fetch_dump()

        logger.info('Beginning digestion of %s. Distributed is %s' % (self.dump, self.distrib))

        # Check to see that there are workers available for distributed tasks.
        if self.distrib and not workers():
            logger.error('Can\'t start distributed digestion, no workers available or MQ server is not available.')
            return

        if self.dump == 'pages':
            if self.distrib:
                # Create async Celery tasks to
                # process pages in parallel.
                # ===
                # The tasks are in a chord, so that
                # after all tasks have been completed,
                # generate TF-IDF representation of all docs.
                # ===
                # Pickle (the default serializer for Celery) has
                # trouble serializing the lxml Element,
                # so first convert it to a string.
                # ===
                # `_t_generate_tfidf` has to have `self` manually
                # passed, and is a bit weird. See its definition below.
                tasks = chord(self._t_process_page.s(tostring(page))
                              for page in self._parse_pages())(self._t_generate_tfidf.s(self, ))
            else:
                # Serially/synchronously process pages.
                docs = [self._process_page(page) for page in self._parse_pages()]

                # Generate TF-IDF representation
                # of all docs upon completion.
                self._generate_tfidf(docs)


    def _generate_tfidf(self, docs):
        """
        Generate the TF-IDF representations for all the digested docs.

        Args:
            | docs (list)       -- a list of docs, where each doc is a tuple of
                                   ( id, [document vector] ).
                                   The "document vector" is a list of the token_ids that
                                   appeared in that document.
                                   e.g. the doc with id 12, which looked like '1 2 4 2 3 4'
                                   would be (12, [1,2,3,4])

        """
        logger.info('Page processing complete. Generating TF-IDF representations.')

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

        # Iterate over all docs
        # the specified docs.
        #if self.distrib:
            ## Save the corpus counts to MongoDB.
            ## MongoDB does not accept integers as keys,
            ## so convert to a list of tuples.
            #corpus_doc = { 'counts': list(corpus_counts.items()) }
            #self.corpus().update({'title': '_corpus_counts'}, {'$set': corpus_doc})
            #if self.silent:
                #tasks = group(self._t_calculate_tfidf.s(doc_id)
                              #for doc_id in doc_ids)
            #else:
                #tasks = chord(self._t_calculate_tfidf.s(doc_id)
                              #for doc_id in doc_ids)(notify.si('TF-IDF calculations completed for %s!' % self.file))
        #else:
            #for doc_id in doc_ids:
                #self._calculate_tfidf(doc_id, corpus_counts)
            #logger.info('TF-IDF calculations completed!')

        for doc_id in doc_ids:
            self._calculate_tfidf(doc_id, corpus_counts)
        logger.info('TF-IDF calculations completed!')

        processed_name = self.url if self.url else self.file
        notify('TF-IDF calculations complete for %s!' % processed_name)


    @celery.task(filter=task_method)
    def _t_generate_tfidf(docs, self):
        """
        The positional argument ordering here is weird,
        with `self` coming last, because of the way
        Celery passes parameters to a class method subtask.
        The *first* argument is the results of the chord's task group,
        and any arguments you pass in manually come *afterwards*.
        """
        self._generate_tfidf(docs)


    def _calculate_tfidf(self, doc_id, corpus_counts):
        """
        General TF-IDF formula:
            j_w[i] = j[i] * log_2(num_docs_corpus / num_docs_term)
        Or, more verbosely:
            tfidf weight of term i in doc j = freq of term i in doc j * log_2(num of docs in corpus/how many docs term i appears in)
        """
        db = self.db()
        doc = db.find({'_id': doc_id})
        tfidf_dict = {}

        # Convert each token's count to its tf-idf value.
        for token_id, token_count in doc['freqs']:
            tfidf_dict[token_id] = token_count * log((self.num_docs/corpus_counts[token_id]), 2)

        # Update the record's `doc` value to the tf-idf representation.
        # Need to convert to a list of tuples,
        # since the db won't take a dict.
        tfidf_doc = list(tfidf_dict.items())
        db.update({'_id': doc['_id']}, {'$set': {'doc': tfidf_doc }})

        return tfidf_doc


    @celery.task(filter=task_method)
    def _t_calculate_tfidf(self, doc_id):
        """
        Celery task for asynchronously calculating TF-IDF.
        """
        corpus_doc = self.corpus().find({'title': '_corpus_counts'})
        corpus_counts = dict(corpus_doc['counts'])
        return self._calculate_tfidf(doc_id, corpus_counts)


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
        category names, and linked page names,
        and store to the database.
        """

        # Log current progress every 10000th doc.
        if self.num_docs % 10000 == 0:
            logger.info('Processing document %s' % self.num_docs)

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

        # Save the doc
        # If it exists, update the existing doc.
        # If not, create it.
        self.db().update({'_id': id}, {'$set': doc})


        # Return the token_ids that were in this document.
        # Used for construction of the global doc counts for terms.
        # Need to tag it with the its doc id; this way we know
        # which page records to update.
        return ( id, list(bag_of_words.keys()) )


        # For exploring the data as separate files.
        #import json
        #json.dump(doc, open('dumps/%s' % title, 'w'), sort_keys=True,
                #indent=4, separators=(',', ': '))


    @celery.task(filter=task_method)
    def _t_process_page(self, elem):
        """
        Celery task for asynchronously processing a page.

        This is conditionally called upon in `self.digest()`.
        """
        # Convert the elem back to an lxml Element,
        # then process.
        return self._process_page(fromstring(elem))


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


    def db(self):
        """
        Returns an interface for this digester's database.

        The database interface cannot be properly serialized for distributed tasks,
        so we can't attach it as an instance variable.
        Instead we just create a new interface when we need it.
        """
        return Adipose(self.database, self.dump)

    def corpus(self):
        return Adipose(self.database, 'corpus_%s' % self.dump)
