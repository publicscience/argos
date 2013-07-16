#!./shallowthought-env/bin/python

DUMP_URL = 'http://dumps.wikimedia.org/enwiki/latest/enwiki-latest-stub-articles10.xml.gz'
DATA_PATH = '../data/wiki/'
NAMESPACE = 'http://www.mediawiki.org/xml/export-0.8/'

from digester import Digester

def process_element(elem):
    print elem.find('{%s}title' % NAMESPACE).text.encode('utf-8')

def main():
    d = Digester('data/wiki/wiki.xml', NAMESPACE)
    d.iterate('page', process_element)

if __name__ == '__main__':
    main()
