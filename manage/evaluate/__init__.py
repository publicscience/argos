import os
import cProfile, pstats

from argos.datastore import db
from argos.core.models import Event, Article
from argos.util.logger import logger
from argos.util.progress import progress_bar

from flask.ext.script import Command

# Logging.
logger = logger(__name__)

class EvaluateCommand(Command):
    """
    Evaluates the precision and accuracy
    of clustering in the application.
    Running this in a production environment
    is not recommended as it modifies the database.
    """
    def run(self):
        evaluate()

def evaluate_clustering():
    """
    Evaluate the clustering algorithm.
    """

    logger.info('Constructing expected clusters and articles...')
    expected_clusters = {}
    articles = []
    all_files = []

    # Collect all appropriate files.
    for dir, subdir, files in os.walk('manage/data/organized_articles'):
        for file in files:
            filepath = os.path.join(dir, file)
            name, ext = os.path.splitext(filepath)
            if ext == '.txt':
                all_files.append((dir, name, filepath))

    # Create articles for appropriate files.
    for dir, name, filepath in all_files:
        category = dir.split('/')[-1]
        f = open(filepath, 'r')
        article = Article(
                text=f.read(),
                title=name.split('/')[-1]
        )
        expected_clusters.setdefault(category, []).append(article)
        articles.append(article)
        progress_bar(len(articles)/len(all_files) * 100)
    print('\n')

    logger.info('Will cluster {0} articles.'.format(len(articles)))
    logger.info('Expecting {0} clusters.'.format(len(expected_clusters.keys())))

    logger.info('Clustering...')
    p = cProfile.Profile()
    clusters = p.runcall(Event.cluster, articles, threshold=0.04, debug=True)

    logger.info('Created {0} clusters.'.format(len(clusters)))

    logger.info('Cluster composition is as follows...')
    for c in clusters:
        logger.info([m.title for m in c.members])

    logger.info('Profiling statistics from the clustering...')
    ps = pstats.Stats(p)
    ps.sort_stats('time').print_stats(10)


def evaluate():
    evaluate_clustering()
