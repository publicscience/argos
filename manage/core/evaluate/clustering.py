"""
Clustering evaluation
=====================

"""

# Override the debug setting
# or it'll log a bunch of stuff.
from argos.conf import APP
APP['DEBUG'] = False

from argos.datastore import db
from argos.core.models import Article, Event, Story
from argos.core.models.cluster import Clusterable
from argos.util.progress import progress_bar

from manage.core.evaluate.patch import start_patches, stop_patches, patch_external
from manage.core.evaluate.report import build_report

import numpy
from sklearn import metrics
from dateutil.parser import parse

import os
import json
import webbrowser
import inspect, importlib
from datetime import datetime
from contextlib import contextmanager
from collections import namedtuple
from itertools import permutations

def make_sim(sim_func, weights):
    def func(self, obj):
        return sim_func(self, obj, weights=weights)
    return func


class Evaluator():
    Label = namedtuple('Label', ['clusterable', 'label'])
    Result = namedtuple('Result', ['composition', 'score'])

    def __init__(self, datapath):
        self.datapath = os.path.expanduser(datapath)
        self.clusterables, self.labels_true, self.expected_clusters = self._load_data()

        weights = [val for val in numpy.linspace(0.0, 1.0, 4.0)]

        self.default_search_grid = {
            # Similarity thresholds
            'threshold': [val for val in numpy.linspace(
                    0.0,
                    1.0,
                    20.0
                )],

            # Similarity strategies (funcs)
            'strategy': self.strategies(),

            'weights': list(permutations(weights))
        }

    def evaluate(self, params_grid=None):
        """
        Run the evaluation over the grid search parameters.
        """
        print('Running clustering...')

        self._reset()
        if params_grid is None: params_grid = self.default_search_grid

        # For the progress bar.
        total_combos = 1
        completed_combos = 0
        for vals in params_grid.values():
            total_combos *= len(vals)
        print('Trying {0} combinations of parameters'.format(total_combos))
        progress_bar(completed_combos/total_combos * 100)

        # Patch things that are time-consuming,
        # but which aren't being evaluated here.
        # In particular, summarization is *REALLY* slow,
        # and not being looked at here, so it's patched out.
        patches = start_patches()
        patches_external = patch_external()

        scores = {}
        clusters = {}

        for strat_func in params_grid['strategy']:
            strat_name = strat_func.__name__
            _scores = {}
            _clusters = {}

            for thresh in params_grid['threshold']:
                _scores[thresh] = {}
                _clusters[thresh] = {}

                for weights in params_grid['weights']:
                    # Run the clustering.
                    _scores[thresh][weights], _clusters[thresh][weights] = self._cluster(strat_func, thresh, weights)

                    self._reset()

                    completed_combos += 1
                    progress_bar(completed_combos/total_combos * 100)

                # Calculate the average score for this threshold.
                _scores[thresh]['AVERAGE'] = sum([_scores[thresh][weights] for weights in _scores[thresh]])/len(_scores[thresh])

            # Calculate the average score for this strategy.
            _scores['AVERAGE'] = sum([_scores[thresh]['AVERAGE'] for thresh in _scores])/len(_scores)

            # Record the results.
            scores[strat_name] = _scores
            clusters[strat_name] = _clusters

        # Stop patches.
        stop_patches(patches)
        stop_patches(patches_external)

        # Calculate bests.
        best_result = self.Result(None, 0)
        worst_result = self.Result(None, 1)
        all_scores = []
        for composition, score in self._get_scores(scores):
            all_scores.append(score)
            if score > best_result.score:
                best_result = self.Result(composition, score)
            if score < worst_result.score:
                worst_result = self.Result(composition, score)
        average_score = sum(all_scores)/len(all_scores)

        # Generate a report.
        report_path = self._generate_report(scores, clusters, best_result, worst_result, average_score)
        print('Report created at {0}.'.format(report_path))

        # Open the report in the browser.
        webbrowser.open('file://{0}'.format(report_path), new=2)

    def _cluster(self, similarity_func, threshold, weights):
        """
        Run the clustering for a particular
        similarity function and threshold.

        Returns the score and lists representing
        the resulting clusters.
        """

        sim_func = make_sim(similarity_func, weights)
        with patch_similarity(self.clusterable_cls, sim_func):
            # Run the clustering.
            self.cluster_cls.cluster(
                self.clusterables,
                threshold=threshold)

            # Get the resulting labels.
            clusters = self.cluster_cls.query.all()
            labels = []
            for clus in clusters:
                labels += [self.Label(c, clus.id) for c in clus.members]

            # Sort the labels to match the self.labels_true sort order,
            # which is the the self.clusterables sort order.
            sort_map = {l.clusterable.id: l for l in labels}
            sorted_labels = [sort_map[c.id] for c in self.clusterables]
            labels_pred = [l.label for l in sorted_labels]

        # Score results and get cluster memberships.
        score = self._score(labels_pred)
        clusters = [c.members.all() for c in clusters]
        return score, clusters

    def _generate_report(self, scores, clusters, best, worst, average):
        """
        Generate an HTML report of the evaluation results.
        """
        now = datetime.now()
        subject = self.cluster_cls.__name__
        strategy_sources = {s.__name__: ''.join(inspect.getsourcelines(s)[0]) for s in self.strategies()}

        return build_report('cluster_report', subject.lower() + '_clustering_' + now.isoformat(), {
            'name': '{0} clustering evaluation'.format(subject),
            'date': now,
            'best': best,
            'worst': worst,
            'average': average,
            'all_clusters': clusters,
            'all_scores': scores,
            'expected': self.expected_clusters,
            'clusterables': self.clusterables,
            'datapath': self.datapath,
            'sources': strategy_sources
        })

    def _get_scores(self, results, composition='', ignore_keys=['AVERAGE']):
        """
        Yields the score values (assumed to be the only
        float dict value) out of a nested dict of scores.
        """
        for key, val in results.items():
            key_ = str(key)

            if key in ignore_keys:
                continue

            if type(val) is dict:
                next_composition = key_ if not composition else composition + ' | ' + key_
                for c, v in self._get_scores(val, next_composition):
                    yield c, v

            elif type(val) in [float, numpy.float64]:
                yield composition + ' | ' + key_, val

            else:
                raise Exception('Unexpected type. Expecting a dict or a float.')

    def _reset(self):
        """
        Reset created clusters.
        """
        raise NotImplementedError

    def _purge(self):
        """
        Resets the evaluation database.
        """
        print('Resetting the database...')
        db.session.close()
        db.drop_all()
        db.create_all()

    def _load_data(self):
        """
        This loads the test data,
        which is pre-labeled,
        and return the data to be clustered
        as well as their expected (true) labels.

        This assumes that the test data is in JSON format,
        structured roughly like so::

            [ // Clusters

                { // A Cluster

                    // members for the cluster and other data

                }
            ]
        """
        patches = patch_external()
        self._purge()

        print('Loading testing data at {0}...'.format(self.datapath))
        data = json.load(open(self.datapath))

        labels_true = []
        expected_clusters = []

        # For the progress bar.
        total = len(data)
        completed = 0
        progress_bar(completed/total * 100)

        for idx, cluster in enumerate(data):

            members = self._process_cluster(cluster)

            expected_clusters.append(members)
            labels_true += [idx for i in range(len(members))]

            completed += 1
            progress_bar(completed/total * 100)

        # What the evaluator will be clustering.
        clusterables = [a for mems in expected_clusters for a in mems]

        db.session.commit()

        stop_patches(patches)

        print('Loaded {0} clusterables (of class {1}). Expecting {2} clusters.'.format(
            len(clusterables),
            self.clusterable_cls.__name__,
            len(expected_clusters)))
        return clusterables, labels_true, expected_clusters


    def _process_cluster(self, cluster):
        """
        This is called from within `_load_data`
        to process an individual cluster from
        the raw test data.

        This needs to return:
            * (list) the members of that cluster
        """
        raise NotImplementedError

    def strategies(self):
        """
        Load in all alternative strategies,
        which are methods with 'similarity' in
        their name.
        """
        strategies_module = importlib.import_module('manage.core.evaluate.strategies.' + self.cluster_cls.__name__.lower())
        strategies = [f[1] for f in inspect.getmembers(strategies_module, inspect.isfunction) if 'similarity' in f[0]]

        # Add the default strategy.
        strategies.append(Clusterable.similarity)

        print('Using {0} different similarity strategies.'.format(len(strategies)))
        return strategies

    def _score(self, labels_pred):
        """
        Score the clustering results.

        These labels to NOT need to be congruent,
        these scoring functions only consider the cluster composition.

        That is::

            self.labels_true = [0,0,0,1,1,1]
            labels_pred = [5,5,5,2,2,2]
            self._score(labels_pred)
            >>> 1.0

        Even though the labels aren't exactly the same,
        all that matters is that the items which belong together
        have been clustered together.
        """
        #return metrics.adjusted_rand_score(self.labels_true, labels_pred)
        #return metrics.v_measure_score(self.labels_true, labels_pred)
        return metrics.adjusted_mutual_info_score(self.labels_true, labels_pred)







class EventEvaluator(Evaluator):
    cluster_cls = Event
    clusterable_cls = Article

    def _process_cluster(self, cluster):
        """
        Expected format of an Event is::
            {
                'title': 'an event title',
                'articles': [{
                    // article representation
                    // ...
                    // MongoDB exported datetimes:
                    'created_at': { '$date': '2014-08-05T19:44:26.069-0400' }
                }]
            }
        """
        event_articles = cluster['articles']
        members = []
        for a_data in event_articles:
            # Handle MongoDB JSON dates.
            for key in ['created_at', 'updated_at']:
                a_data[key] = parse(a_data[key]['$date'])

            article = Article(**a_data)
            db.session.add(article)

            members.append(article)
        return members

    def _reset(self):
        Event.query.delete()
        db.session.commit()


class StoryEvaluator(Evaluator):
    cluster_cls = Story
    clusterable_cls = Event

    def _process_cluster(self, cluster):
        """
        Expected format of a Story is::

            {
                'title': 'an story title',
                'events': [{
                    // event representation,
                    // see `EventEvaluator#_load_data`
                }]
            }
        """
        story_events = cluster['events']
        members = []
        for e_data in story_events:
            articles = []
            for a_data in e_data['articles']:
                # Handle MongoDB JSON dates.
                for key in ['created_at', 'updated_at']:
                    a_data[key] = parse(a_data[key]['$date'])
                article = Article(**a_data)
                articles.append(article)
            event = Event(articles)
            event.title = e_data['title']
            db.session.add(event)

            members.append(event)
        return members

    def _reset(self):
        Story.query.delete()
        db.session.commit()







@contextmanager
def patch_similarity(cls, new_func):
    """
    Patch the `similarity` method for
    a class.
    """
    tmp = cls.similarity
    cls.similarity = new_func
    yield
    cls.similarity = tmp

