#!../shallowthought-env/bin/python

'''
Digester
==============

Processes Wikipedia dumps.
'''

from lxml import etree
import gullet

DUMP_URL = 'http://dumps.wikimedia.org/enwiki/latest/enwiki-latest-stub-articles10.xml.gz'
DATA_PATH = '../data/wiki/'





def main():
    #gullet.download(DUMP_URL,DATA_PATH)

    namespace = '{http://www.mediawiki.org/xml/export-0.8/}'
    infile = '../data/wiki/wiki.xml'

    # Create element context for a specified tag.
    context = etree.iterparse(infile, events=('end',), tag='%spage' % namespace)
    out = open('titles.txt', 'w')

    for event, elem in context:
        print elem.find('{0}title'.format(namespace))
        #out.write('%s\n' % elem.text.encode('utf-8'))

        # Clear the elem, since we're done with it
        elem.clear()

        # Eliminate now-empty refs from the root node
        # to the specified tag.
        while elem.getprevious() is not None:
            del elem.getparent()[0]

    # Clean up the context
    del context

    out.close()
    return 0

if __name__ == '__main__':
    main()
