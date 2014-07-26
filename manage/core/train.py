import json

from flask.ext.script import Command, Option

from argos.core import brain


class TrainVectorizerCommand(Command):
    """
    Trains and serializes (pickles) a vectorizing pipeline
    based on training data.
    """
    option_list = (
        Option(dest='filepath', type=str),
    )
    def run(self, filepath):
        train(filepath)

def train(filepath):
    print('Loading training data from {0}...'.format(filepath))
    training_file = open(filepath, 'r')
    training_data = json.load(training_file)

    docs = ['{0} {1}'.format(d['title'], d['text']) for d in training_data]
    brain.vectorize.train(docs)
