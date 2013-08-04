#!./shallowthought-env/bin/python

DUMP_URL = 'http://dumps.wikimedia.org/enwiki/latest/enwiki-latest-stub-articles10.xml.gz'
DATA_PATH = '../data/wiki/'
NAMESPACE = 'http://www.mediawiki.org/xml/export-0.8/'

import string
from digester import Digester, Adipose
from mwlib import parser
from mwlib.refine.compat import parse_txt

def main():
    d = Digester('data/wiki/article.xml', NAMESPACE)
    #a = Adipose('test', 'titles')

    def clean(text):
        """
        Cleans up MediaWiki text of markup.
        Currently a 'naive' version in that
        it just strips *all* punctuation.

        Will eventually want to strip out unnecessary
        markup syntax as well, such as "File:" and
        "Category".

        Args:
            | text (str)    -- the MediaWiki text to cleanup. Must be utf-8 encoded.
        """
        replace_punctuation = string.maketrans(string.punctuation, ' '*len(string.punctuation))
        return text.translate(replace_punctuation)

    def process_element(elem):
        text = elem.find('{%s}revision' % NAMESPACE).find('{%s}text' % NAMESPACE).text.encode('utf-8')

        print clean(text)

        #a.empty()
        #a.add(data)

    d.iterate('page', process_element)

if __name__ == '__main__':
    main()
