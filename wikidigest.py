#!./shallowthought-env/bin/python

DUMP_URL = 'http://dumps.wikimedia.org/enwiki/latest/enwiki-latest-stub-articles10.xml.gz'
DATA_PATH = '../data/wiki/'
NAMESPACE = 'http://www.mediawiki.org/xml/export-0.8/'

from digester import Digester, Adipose

def main():
    d = Digester('data/wiki/wiki.xml', NAMESPACE)
    a = Adipose('test', 'titles')

    def process_element(elem):
        data = {'title': elem.find('{%s}title' % NAMESPACE).text.encode('utf-8')}
        a.empty()
        a.add(data)

    d.iterate('page', process_element)

if __name__ == '__main__':
    main()
