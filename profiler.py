"""
Profiler
==============

A basic profiler to measure performance
and identify bottlenecks.
"""

import cProfile, pstats
from digester.wikidigester import WikiDigester
from adipose import Adipose

def profile_wikidigester():
    # Create a WikiDigester
    w = WikiDigester('data/wiki/wiki_profile.xml', 'pages', db='test')
    w.purge()

    print('Profiling WikiDigester...')

    p = cProfile.Profile()
    p.runctx('w.digest()', None, {'w': w})
    ps = pstats.Stats(p)

    # See which specific func takes the most time.
    #ps.strip_dirs().sort_stats('time').print_stats(10)

    # See which top-level funcs takes the most time.
    ps.sort_stats('cumulative').print_stats(10)

def profile_wikidigester_distrib():
    # Create a WikiDigester
    w = WikiDigester('data/wiki/wiki_profile.xml', 'pages', distrib=True)
    w.purge()

    print('Profiling WikiDigester distributed...')

    p = cProfile.Profile()
    p.runctx('w.digest()', None, {'w': w})
    ps = pstats.Stats(p)

    # See which top-level funcs takes the most time.
    ps.sort_stats('cumulative').print_stats(10)

if __name__ == '__main__':
    #profile_wikidigester()
    profile_wikidigester_distrib()
