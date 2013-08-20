#!dev-env/bin/python

from digester.wikidigester import WikiDigester

def main():
    w = WikiDigester('data/wiki/wiki.xml', 'pages')
    w.digest()

if __name__ == '__main__':
    main()
