#!dev-env/bin/python

from digester.wikidigester import WikiDigester
from adipose import Adipose

def main():
    w = WikiDigester('data/wiki/wiki_profile.xml', 'pages', distrib=True)
    w.purge()
    w.digest()

if __name__ == '__main__':
    main()
