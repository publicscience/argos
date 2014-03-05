"""
Digester
==============

Processes XML or bzipped XML dumps.
"""

from argos.util import gullet

from lxml import etree

import os
import bz2

class Digester:
    """
    Processes ("digests") XML dumps.
    A Digester works with a single XML file.
    It also supports bzipped XML files.

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
        self.namespace = '{{0}}'.format(namespace)


    def iterate(self, tag):
        """
        A generator that iterates over an XML context for a specific tag,
        yielding each element of the matching tag..
        Can handle either XML or bzipped XML (.bz2).

        Args:
            | tag (str)                 -- the target tag/element to find.

        Yields:
            | elem (lxml Element)       -- the target element.
        """

        # Check if the file is bzipped
        # and handle accordingly.
        ext = os.path.splitext(self.file)[1]
        if ext == '.bz2':
            file = bz2.BZ2File(self.file, 'r')
        else:
            file = self.file


        # Create the iterparse context
        context = etree.iterparse(file, events=('end',), tag='{0}{1}'.format(self.namespace, tag))

        # Iterate
        # http://ibm.co/17rvZ
        for event, elem in context:

            # Yield the element.
            yield elem

            # Clear the elem, since we're done with it
            elem.clear()

            # Eliminate now-empty refs from the root node
            # to the specified tag.
            while elem.getprevious() is not None:
                del elem.getparent()[0]

        # Clean up the context
        del context


    def _find(self, elem, *tags):
        """
        Finds a particular subelement of an element.

        Args:
            | elem (lxml Element)  -- the element to search through.
            | *tags (strs)         -- the tag names to use. See below for clarification.

        Returns:
            | lxml Element -- the target element.

        You need to provide the tags that lead to it.
        For example, the `text` element is contained
        in the `revision` element, so this method would
        be used like so::

            self._find(elem, 'revision', 'text')

        This method is meant to replace chaining calls
        like this::

            text_el = elem.find('{{0}}revision'.format(NAMESPACE)).find('{{0}}text'.format(NAMESPACE))
        """
        for tag in tags:
            elem = elem.find('{0}{1}'.format(self.namespace, tag))
        return elem


    def download(self, url):
        """
        Downloads a file from the specified URL to replace
        this Digester's current file.

        Args:
            | url (str) -- the url of the file to download
        """

        # Get save directory for download.
        save_path = os.path.dirname(self.file)

        # Download!
        saved_filepath = gullet.download(url, save_path)

        # Rename downloaded file to match Digester's file.
        os.rename(saved_filepath, self.file)
