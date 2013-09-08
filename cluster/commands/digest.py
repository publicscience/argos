from ..digest.wikidigester import WikiDigester

def main():
    w = WikiDigester('/tmp/wiki.xml', 'pages', distrib=True, db='wikidump')

    # Empty out database.
    w.purge()

    # Fetch dump if necessary.
    w.fetch_dump()

    # Digest.
    w.digest()

if __name__ == '__main__':
    main()
