#!../shallowthought-env/bin/python

"""
Digester
==============

Processes Wikipedia (XML) dumps.
"""

from lxml import etree
from adipose import Adipose
import gullet

DUMP_URL = 'http://dumps.wikimedia.org/enwiki/latest/enwiki-latest-stub-articles10.xml.gz'
DATA_PATH = '../data/wiki/'
NAMESPACE = '{http://www.mediawiki.org/xml/export-0.8/}'


def main():
    #gullet.download(DUMP_URL,DATA_PATH)

    infile = '%swiki.xml' % DATA_PATH
    # Create element context for a specified tag.
    context = etree.iterparse(infile, events=('end',), tag='%spage' % NAMESPACE)
    iterate(context, process_element)
    return 0

class Digester:
    """
    Processes ("digests") Wikipedia XML dumps.
    """

    def __init__(self, data, namespace):
        """
        Initialize the Digester with a namespace.
        """


    def process_element(elem):
        print elem.find('%stitle' % NAMESPACE).text.encode('utf-8')

    def create_context(infile, tag):
        """
        Creates an iterparse context for a tag.

        Args:
            | infile (str)  -- path to the XML file to read.
            | tag (str)     -- the tag name to search for.
        """
        return etree.iterparse(infile, events=('end',), tag='%s%s' % (NAMESPACE, tag))

    def iterate(context, process_element):
        """
        Iterates over an XML context. (http://ibm.co/17rvZ)

        Args:
            | context (obj)             -- the lxml iterparse object to iterate over
            | process_element (func)    -- function to call on each element

        Example::

            # assuming we have defined a func 'process_element()'
            infile = '/path/to/some/file'
            context = create_context(infile, 'page')
            iterate(context, process_element)
        """

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

if __name__ == '__main__':
    main()
