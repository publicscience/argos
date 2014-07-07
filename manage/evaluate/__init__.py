"""
Evaluate
==========
For evaluating algorithmic quality.
Can seed some hand-selected data
for this purpose.
"""

from flask.ext.script import Command, Option

from manage.evaluate.prepare import generate, seed
from manage.evaluate.clustering import evaluate_events, evaluate_stories

class EvaluateCommand(Command):
    option_list = (
        Option(dest='cmd'),
        Option('--step', '-s', dest='step', default=0.05, type=float),
        Option('--min_threshold', '-min', dest='min_threshold', default=0.0, type=float),
        Option('--max_threshold', '-max', dest='max_threshold', default=1.0, type=float),
    )
    def run(self, cmd, step, min_threshold, max_threshold):
        if cmd == 'prepare':
            generate()
            seed()
        elif cmd == 'event':
            evaluate_events(step, min_threshold, max_threshold)
        elif cmd == 'story':
            evaluate_stories(step, min_threshold, max_threshold)
        else:
            print('Unrecognized command, use either `prepare`, `event`, or `story`.')
