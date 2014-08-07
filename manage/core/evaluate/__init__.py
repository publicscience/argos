"""
Evaluate
==========
For evaluating algorithmic quality.
"""

from flask.ext.script import Command, Option

from manage.core.evaluate.clustering import EventEvaluator, StoryEvaluator

class EvaluateEventCommand(Command):
    option_list = (
        Option('--datapath', '-d', dest='datapath', default='all', type=str),
        Option('--step', '-s', dest='step', default=0.05, type=float),
        Option('--min_threshold', '-min', dest='min_threshold', default=0.0, type=float),
        Option('--max_threshold', '-max', dest='max_threshold', default=1.0, type=float),
    )
    def run(self, datapath, step, min_threshold, max_threshold):
        if datapath == 'all':
            basepath = 'manage/core/evaluate/data/event'
            for dpath in [basepath+'/handpicked.json', basepath+'/wikinews.json']:
                e = EventEvaluator(dpath)
                e.evaluate()
        else:
            e = EventEvaluator(datapath)
            e.evaluate()

class EvaluateStoryCommand(Command):
    option_list = (
        Option('--datapath', '-d', dest='datapath', default='all', type=str),
        Option('--step', '-s', dest='step', default=0.05, type=float),
        Option('--min_threshold', '-min', dest='min_threshold', default=0.0, type=float),
        Option('--max_threshold', '-max', dest='max_threshold', default=1.0, type=float),
    )
    def run(self, datapath, step, min_threshold, max_threshold):
        if datapath == 'all':
            basepath = 'manage/core/evaluate/data/story'
            for dpath in [basepath+'/handpicked.json']:
                e = StoryEvaluator(dpath)
                e.evaluate()
        else:
            e = StoryEvaluator(datapath)
            e.evaluate()
