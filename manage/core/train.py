import json

from flask.ext.script import Command, Option

from argos.core import brain
from galaxy import concept, vector

class TrainVectorizerCommand(Command):
    """
    Trains and serializes (pickles) a vectorizing pipeline
    based on training data.
    """
    option_list = (
        Option(dest='pipetype', type=str),
        Option(dest='datapath', type=str),
    )
    def run(self, datapath, pipetype):
        print('Loading training data from {0}...'.format(datapath))
        with open(datapath, 'r') as f:
            training_data = json.load(f)
            docs = ['{0} {1}'.format(d['title'], d['text']) for d in training_data]

        # These train to the PIPELINE_PATH specified in argos.conf.app
        if pipetype == 'bow':
            vector.train(docs)

        if pipetype in ['stanford', 'spotlight', 'keyword']:
            concept.train(docs, pipetype=pipetype)
