"""
Profile
==============

A basic profiler to measure performance
and identify bottlenecks.
"""

import cProfile, pstats

from argos.core.digester.wikidigester import WikiDigester

from argos.datastore import db

from argos.core.brain import vectorize
from argos.core.brain.summarize import summarize, multisummarize
from argos.core.models import Article, Event

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

def profile_vectorize():
    print('argos.core.brain.vectorize')
    doc = open('tests/data/multidoc/1.txt', 'r').read()
    profile_cmd('v(d)', None, {'v': vectorize, 'd': doc})

def profile_summarize():
    print('argos.core.brain.summarize.summarize')
    doc = open('tests/data/multidoc/1.txt', 'r').read()
    title = 'This is a title'
    profile_cmd('s(t, d)', None, {'s': summarize, 't': title, 'd': doc})

def profile_multisummarize():
    print('argos.core.brain.summarize.multisummarize')
    docs = [open('tests/data/multidoc/{0}.txt'.format(i), 'r').read() for i in range(1,4)]
    profile_cmd('s(d)', None, {'s': multisummarize, 'd': docs})

def profile_event_clustering():
    print('argos.core.models.event.Event.cluster')
    docs = [open('tests/data/multidoc/{0}.txt'.format(i), 'r').read() for i in range(1,4)]
    articles = [Article(title='Test title', text=doc) for doc in docs]
    db.session.add_all(articles)
    db.session.commit()
    profile_cmd('E.cluster(a)', None, {'E': Event, 'a': articles})

def profile():
    profile_vectorize()
    profile_summarize()
    profile_multisummarize()
    profile_event_clustering()


def profile_cmd(*args):
    p = cProfile.Profile()
    p.runctx(*args)
    ps = pstats.Stats(p)

    # See which specific func takes the most time.
    ps.sort_stats('time').print_stats(10)
