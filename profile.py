import cProfile
from wikidigester import WikiDigester
from adipose import Adipose

def profile_wikidigester():
    # Create a WikiDigester
    w = WikiDigester('data/wiki/wiki.xml', 'pages')

    # Setup a database.
    db = Adipose('test', 'pages')
    db.empty()

    # Set WikiDigester to use this database.
    w.db = db

    print('Profiling WikiDigester...')
    cProfile.run(w.digest())

if __name__ == '__main__':
    profile_wikidigester()
