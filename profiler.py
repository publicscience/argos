import cProfile, pstats
from wikidigester import WikiDigester
from adipose import Adipose

def profile_wikidigester():
    # Create a WikiDigester
    w = WikiDigester('data/wiki/wiki_profile.xml', 'pages')

    # Setup a database.
    db = Adipose('test', 'pages')
    db.empty()

    # Set WikiDigester to use this database.
    w.db = db

    print('Profiling WikiDigester...')

    p = cProfile.Profile()
    p.runctx('w.digest()', None, {'w': w})
    ps = pstats.Stats(p)

    # See which specific func takes the most time.
    #ps.strip_dirs().sort_stats('time').print_stats(10)

    # See which top-level funcs takes the most time.
    ps.sort_stats('cumulative').print_stats(10)


if __name__ == '__main__':
    profile_wikidigester()
