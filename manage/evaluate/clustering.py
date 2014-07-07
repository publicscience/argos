"""
Clustering
==========
Evaluate article=>event
and event=>story clustering.
"""

from argos.datastore import db
from argos.core.models import Article, Event, Story
from argos.util.progress import progress_bar

import json
import numpy
import inspect, importlib
from datetime import datetime
from contextlib import contextmanager
from colorama import Fore

from manage.evaluate.patch import start_patches, stop_patches
from manage.evaluate.report import build_report

def evaluate_events(step, min_threshold, max_threshold):
    """
    Evaluate the event clustering algorithm.
    """

    # Load the annotated data.
    print('Assembling expected article clusters...')
    expected_events = {}
    seed = json.load(open('manage/data/evaluation/seed.json'))
    for source_name, source_data in seed['sources'].items():
        for feed_url, raw_articles in source_data['feeds'].items():
            for article_data in raw_articles:
                article = Article.query.filter_by(ext_url=article_data['ext_url']).first()
                event_id = article_data['event']

                # Create the list for this event,
                # if it doesn't already exist.
                if not expected_events.get(event_id, False):
                    expected_events[event_id] = []

                # Keep track of which articles are
                # supposed to be clustered together.
                expected_events[event_id].append(article)
    print('\nExpecting {0}{1}{2} events.'.format(Fore.RED, len(expected_events), Fore.RESET))

    e = Evaluator(Event, Article, expected_events, step, min_threshold, max_threshold)
    e.evaluate()

def evaluate_stories(step, min_threshold, max_threshold):
    """
    Evaluate the story clustering algorithm.
    """

    # Load the annotated data and create "perfect" article clusters.
    print('Assembling expected article clusters ("perfect" events)...')
    expected_events = {}
    expected_stories = {}
    seed = json.load(open('manage/data/evaluation/seed.json'))
    for source_name, source_data in seed['sources'].items():
        for feed_url, raw_articles in source_data['feeds'].items():
            for article_data in raw_articles:
                article = Article.query.filter_by(ext_url=article_data['ext_url']).first()
                event_id = article_data['event']

                # Create the list for this event,
                # if it doesn't already exist.
                if not expected_events.get(event_id, False):
                    expected_events[event_id] = []

                # Keep track of which articles are
                # supposed to be clustered together.
                expected_events[event_id].append(article)

    total_events = len(expected_events)
    completed_events = 0
    for story_name, events in seed['stories'].items():

        # Create the list for this story,
        # if it doesn't already exist.
        if not expected_stories.get(story_name, False):
            expected_stories[story_name] = []

        progress_bar(completed_events/total_events * 100)

        for event_id, event_title in events.items():
            # Create an event out of the annotated members.
            event = Event(expected_events[int(event_id)])

            # Manually set the titles for easier referencing.
            event.title = '[{0}{1}{2}] {3}'.format(Fore.BLUE, story_name.upper(), Fore.RESET, event_title)

            db.session.add(event)

            # Progress bar, for sanity.
            completed_events += 1
            progress_bar(completed_events/total_events * 100)

            # Keep track of which story this event is
            # supposed to belong to.
            expected_stories[story_name].append(event)
    db.session.commit()
    print('\nExpecting {0}{1}{2} stories.'.format(Fore.RED, len(expected_stories), Fore.RESET))

    e = Evaluator(Story, Event, expected_stories, step, min_threshold, max_threshold)
    e.evaluate()

class Evaluator():
    def __init__(self, cluster_cls, clusterable_cls, expected_clusters, step, min_threshold, max_threshold):
        self.cluster_cls = cluster_cls
        self.cluster_name = cluster_cls.__name__
        self.clusterable_cls = clusterable_cls
        self.clusterable_name = clusterable_cls.__name__
        self.expected_clusters = expected_clusters
        self.step = step
        self.min_threshold = min_threshold
        self.max_threshold = max_threshold

    def evaluate(self):
        clean()

        # Patch things that are time-consuming,
        # but which aren't being evaluated here.
        # In particular, summarization is *REALLY* slow,
        # and not being looked at here, so it's patched out.
        patches = start_patches()

        # Load in all alternative strategies,
        # which are methods with 'similarity' in
        # their name.
        strategies_module = importlib.import_module('manage.evaluate.strategies.' + self.cluster_name.lower())
        strategies = [f for f in inspect.getmembers(strategies_module, inspect.isfunction) if 'similarity' in f[0]]
        print('Using {0} different similarity strategies.'.format(len(strategies) + 1)) # +1 including default strategy.

        clusterables = self.clusterable_cls.query.all()

        # Run the clustering at the varying thresholds
        # and collect the scores, cluster compositions,
        # and best threshold/scores for each strategy.
        all_scores = {}
        all_results = {}
        best_thresholds = {}

        # Run with the default (currently implemented) similarity function.
        print('Running with default strategy...')
        all_scores['default'], all_results['default'] = self._cluster_across_thresholds(clusterables)
        best_thresholds['default'] = max(all_scores['default'], key=all_scores['default'].get)

        # Run the defined threshold spread with each alternate strategy.
        for (strategy_name, strategy_func) in strategies:
            print('Running with strategy: {0}'.format(strategy_name))
            with patch_similarity(self.clusterable_cls, strategy_func):
                all_scores[strategy_name], all_results[strategy_name] = self._cluster_across_thresholds(clusterables)
                best_thresholds[strategy_name] = max(all_scores[strategy_name], key=all_scores[strategy_name].get)


        # Get the best score.
        best = { 'score': 0 }
        for strategy, threshold in best_thresholds.items():
            score = all_scores[strategy][threshold]
            if score > best['score']:
                best['score'] = score
                best['strategy'] = strategy
                best['threshold'] = threshold
        print('{0}The strategy {1}, with threshold {2}, had the best score of {3}.{4}'.format(Fore.GREEN, best['strategy'], best['threshold'], best['score'], Fore.RESET))

        # Disable patches.
        stop_patches(patches)

        # Build report.
        now = datetime.now()
        build_report('cluster_report', self.cluster_name.lower() + '_clustering_' + now.isoformat(), {
            'name': 'Evaluate {0} clustering'.format(self.cluster_name),
            'date': now,
            'all_results': all_results,
            'all_scores': all_scores,
            'best': best,
            'expected': self.expected_clusters
        })

        # Cleanup
        print('\nCleaning up...')
        clean()

        print('Done.')



    def _cluster_across_thresholds(self, clusterables):
        all_scores, all_clusters = {}, {}
        for threshold in numpy.linspace(self.min_threshold, self.max_threshold, (self.max_threshold-self.min_threshold)/self.step):
            print('\nClustering with threshold {0}{1}{2}'.format(Fore.YELLOW, threshold, Fore.RESET))

            self.cluster_cls.cluster(clusterables, threshold=threshold, debug=False)

            num_clusters = self.cluster_cls.query.count()
            print('Created {0}{1}{2} {3}s:'.format(Fore.YELLOW, num_clusters, Fore.RESET, self.cluster_name))
            print('{0}---{1}'.format(Fore.RED, Fore.RESET))

            # Evaluate the algorithmic quality.
            # This could use refining!
            created_clusters = self.cluster_cls.query.all()
            scores = []
            clusters = []
            for cluster in created_clusters:
                # So we can inspect the cluster compositions.
                members = set(cluster.members)
                clusters.append(members)
                print(members)

                score = score_cluster(cluster, self.expected_clusters)
                scores.append(score)

            print('{0}---{1}'.format(Fore.RED, Fore.RESET))

            # Tweak the score so that the closer it is to 1, the better.
            final_score = 1/(sum(scores) + 1)
            print('Final score was {0}{1}{2}\n'.format(Fore.GREEN, final_score, Fore.RESET))

            # Save the score and cluster compositions.
            all_scores[threshold], all_clusters[threshold] = final_score, clusters

            # Reset clusters.
            self.cluster_cls.query.delete()

        return all_scores, all_clusters




def score_cluster(cluster, expected_clusters):
    """
    Gives a score for a cluster depending on
    how different it is from the expected clusters.

    It just tries to find the smallest difference,
    i.e. it looks for the cluster which overlaps with it
    the most and returns how many members differ between the two.
    """
    # The lower the diff, the better.
    diffs = [len(set(cluster.members).symmetric_difference(set(expected))) for expected in expected_clusters.values()]

    # Get the minimum difference.
    return min(diffs)

def clean():
    Story.query.delete()
    Event.query.delete()

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
