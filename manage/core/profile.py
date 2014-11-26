"""
Profile
==============

A basic profiler to measure performance
and identify bottlenecks.
"""

import cProfile, pstats

from argos.core.brain.summarizer import summarize, multisummarize

from flask.ext.script import Command

class ProfileCommand(Command):
    """
    Profiles various parts of the application.
    Running this in a production environment
    is not recommended as it modifies the database.
    """
    def run(self):
        profile()

def profile_summarize():
    print('argos.core.brain.summarizer.summarize')
    doc = open('tests/data/multidoc/1.txt', 'r').read()
    title = 'This is a title'
    profile_cmd('s(t, d)', None, {'s': summarize, 't': title, 'd': doc})

def profile_multisummarize():
    print('argos.core.brain.summarizer.multisummarize')
    docs = [open('tests/data/multidoc/{0}.txt'.format(i), 'r').read() for i in range(1,4)]
    profile_cmd('s(d)', None, {'s': multisummarize, 'd': docs})

def profile():
    profile_summarize()
    profile_multisummarize()

def profile_cmd(*args):
    p = cProfile.Profile()
    p.runctx(*args)
    ps = pstats.Stats(p)

    # See which specific func takes the most time.
    ps.sort_stats('time').print_stats(10)
