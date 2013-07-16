#!../shallowthought-env/bin/python

'''
Digester
==============

Processes Wikipedia dumps.
'''

from lxml import etree
import simplejson as json
import gullet

DUMP_URL = 'http://dumps.wikimedia.org/enwiki/latest/enwiki-latest-stub-articles10.xml.gz'
DATA_PATH = '../data/wiki/'
NAMESPACE = '{http://www.mediawiki.org/xml/export-0.8/}'

def main():
    #gullet.download(DUMP_URL,DATA_PATH)

    infile = '%swiki.xml' % DATA_PATH
    context = etree.iterparse(infile, events=('end',), tag='%spage' % NAMESPACE)
    iterate(context, process_element)
    return 0

def process_element(elem):
    print elem.find('%stitle' % NAMESPACE).text.encode('utf-8')

def iterate(context, process_element):
    # Credit: Liza Daly (http://ibm.co/17rvZ)
    # Create element context for a specified tag.
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
