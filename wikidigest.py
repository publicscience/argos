#!./shallowthought-env/bin/python

DUMP_URL = 'http://dumps.wikimedia.org/enwiki/latest/enwiki-latest-stub-articles10.xml.gz'
DATA_PATH = '../data/wiki/'
NAMESPACE = 'http://www.mediawiki.org/xml/export-0.8/'

from digester import Digester, Adipose
import re

def main():
    d = Digester('data/wiki/article.xml', NAMESPACE)
    #a = Adipose('test', 'titles')

    def process_element(elem):
        print elem
        #data = {'title': elem.find('{%s}title' % NAMESPACE).text.encode('utf-8')}

        # This extracts the page link text (i.e. the text that links to other pages) from an article.
        text = elem.find('{%s}revision' % NAMESPACE).find('{%s}text' % NAMESPACE).text.encode('utf-8')
        print re.findall('(?<=\[\[)[^a-z*:|File:][^\]|#]*(?=\|)|(?<=\[\[)[^a-z*:|File:][^\]|#]*(?=\]\])', text)

        #a.empty()
        #a.add(data)

    d.iterate('page', process_element)

if __name__ == '__main__':
    main()
