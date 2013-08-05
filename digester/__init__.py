"""
Digester
==============

Processes XML dumps.
"""

from lxml import etree
from adipose import Adipose
import gullet
import os
import bz2

class Digester:
    """
    Processes ("digests") XML dumps.
    A Digester works with a single XML file.

    Example::

        # Digest the 'page' elements in wiki.xml.
        # Assume we have defined some func 'process_element(elem)'
        d = Digester('../data/wiki/wiki.xml', 'http://www.mediawiki.org/xml/export-0.8/')
        d.iterate('page', process_element)
    """

    def __init__(self, file, namespace):
        """
        Initialize the Digester with a file and a namespace.

        Args:
            | file (str)        -- path to XML file (or bzipped XML) to digest.
            | namespace (str)   -- namespace of the file.
        """
        self.file = file
        self.namespace = '{%s}' % namespace


    def iterate(self, tag, process_element):
        """
        Iterates over an XML context for a specific tag.
        Can handle either XML or bzipped XML (.bz2)

        Args:
            | tag (str)                 -- the tag/element to operate on
            | process_element (func)    -- function to call on each element

        If you need to process multiple tags, it's suggested that you specify
        a parent tag, and then `find` the other tags in your `process_element`
        function (see example below).

        Example `process_element`::

            def process_element(elem):
                print elem.find('{%s}title' % namespace).text.encode('utf-8')
        """

        # If bzip (bz2)...
        ext = os.path.splitext(self.file)[1]
        if ext == '.bz2':
            file = bz2.BZ2File(self.file, 'r')
        else:
            file = self.file


        # Create the iterparse context
        context = etree.iterparse(file, events=('end',), tag='%s%s' % (self.namespace, tag))

        # Iterate
        # http://ibm.co/17rvZ
        for event, elem in context:
            # Run process_element on the element.
            process_element(elem)

            # Clear the elem, since we're done with it
            elem.clear()

            # Eliminate now-empty refs from the root node
            # to the specified tag.
            while elem.getprevious() is not None:
                del elem.getparent()[0]

        # Clean up the context
        del context


    def download(self, dump):
        """
        Downloads a file from the specified URL to replace
        this Digester's current file.

        Args:
            | dump (str) -- the name of the dump ('abstract', 'pagelinks', 'pages-articles')
        """

        dumps = {
                    'base': 'http://dumps.wikimedia.org/enwiki/latest/',
                    'abstract': 'enwiki-latest-abstract.xml',
                    'pagelinks': 'enwiki-latest-pagelinks.sql.gz',
                    'pages-articles': 'enwiki-latest-pages-articles.xml.bz2'
                }

        # Build full url.
        url = '%s%s' % (dumps['base'], dumps[dump])

        # Get save directory for download.
        save_path = os.path.dirname(self.file)

        # Download!
        gullet.download(url, save_path)

        # Rename downloaded file to match Digester's file.
        os.rename(file, self.file)
