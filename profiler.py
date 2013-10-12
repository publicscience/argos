"""
Profiler
==============

A basic profiler to measure performance
and identify bottlenecks.
"""

import cProfile, pstats
import brain
from digester.wikidigester import WikiDigester
from adipose import Adipose

def profile_wikidigester():
    # Create a WikiDigester
    part = 'http://dumps.wikimedia.org/enwiki/latest/enwiki-latest-pages-articles1.xml-p000000010p000010000.bz2'
    w = WikiDigester('/tmp/wikitest.xml.bz2', db='wikitest', url=part)

    w.purge()

    print('Profiling WikiDigester...')

    p = cProfile.Profile()
    p.runctx('w.digest()', None, {'w': w})
    ps = pstats.Stats(p)

    # See which specific func takes the most time.
    ps.sort_stats('time').print_stats(10)

if __name__ == '__main__':
    profile_wikidigester()
