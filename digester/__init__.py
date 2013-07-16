"""
Digester
==============

Processes XML dumps.
"""

from lxml import etree
from adipose import Adipose
import gullet

class Digester:
    """
    Processes ("digests") XML dumps.
    A Digester works with a single XML file.

    Example::

        # Digest the 'page' elements in wiki.xml.
        # Assume we have defined some func 'process_element()'
        d = Digester('../data/wiki/wiki.xml', 'http://www.mediawiki.org/xml/export-0.8/')
        d.iterate('page', process_element)
    """

    def __init__(self, file, namespace):
        """
        Initialize the Digester with a file and a namespace.

        Args:
            | file (str)        -- path to XML file to digest.
            | namespace (str)   -- namespace of the file.
        """
        self.file = file
        self.namespace = '{%s}' % namespace

    def download(url):
        """
        Downloads a file from the specified URL to replace
        this Digester's current file.

        Args:
            | url (str) -- the url to download.
        """
        gullet.download(file, self.file)

    def iterate(tag, process_element):
        """
        Iterates over an XML context for a specific tag. (http://ibm.co/17rvZ)

        Args:
            | tag (str)                 -- the tag/element to operate on
            | process_element (func)    -- function to call on each element
        """

        # Create the iterparse context
        context = etree.iterparse(self.file, events=('end',), tag='%s%s' % (self.namespace, tag))

        # Iterate
        for event, elem in context:
            process_element(elem)

            # Clear the elem, since we're done with it
            elem.clear()

            # Eliminate now-empty refs from the root node
            # to the specified tag.
            while elem.getprevious() is not None:
                del elem.getparent()[0]

        # Clean up the context
        del context
