"""
Digest (Gut) Check
==============

A small test digestion to see if distributed
digestion works, using a small part of the Wikipedia
pages-articles dump.
"""

from digester.wikidigester import WikiDigesterDistributed

def main():
    part = 'http://dumps.wikimedia.org/enwiki/latest/enwiki-latest-pages-articles1.xml-p000000010p000010000.bz2'
    w = WikiDigesterDistributed('/tmp/wikitest.xml.bz2', db='wikitest', url=part)

    # Empty out database.
    w.purge()

    # Digest.
    w.digest()

if __name__ == '__main__':
    main()
