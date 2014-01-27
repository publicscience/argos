import os
import cProfile, pstats
from app import db
from brain import cluster
from models import Cluster, Article

# Logging.
from logger import logger
logger = logger(__name__)


def evaluate_clustering():
    """
    Evaluate the clustering algorithm.
    """

    logger.info('Constructing expected clusters and articles...')
    expected_clusters = {}
    articles = []
    for dir, subdir, files in os.walk('manage/cluster_evaluation/organized_articles'):
        for file in files:
            filepath = os.path.join(dir, file)
            name, ext = os.path.splitext(filepath)
            if ext == '.txt':
                category = dir.split('/')[-1]
                f = open(filepath, 'r')
                article = Article(
                        text=f.read(),
                        title=name.split('/')[-1]
                )
                expected_clusters.setdefault(category, []).append(article)
                articles.append(article)

    logger.info('Will cluster {0} articles.'.format(len(articles)))
    logger.info('Expecting {0} clusters.'.format(len(expected_clusters.keys())))

    logger.info('Clustering...')
    p = cProfile.Profile()
    #clusters = cluster.cluster(articles, debug=True, threshold=0.04)
    clusters = p.runcall(cluster.cluster, articles, debug=True, threshold=0.04)

    logger.info('Created {0} clusters.'.format(len(clusters)))

    logger.info('Cluster composition is as follows...')
    for c in clusters:
        logger.info([m.title for m in c.members])

    logger.info('Profiling statistics from the clustering...')
    ps = pstats.Stats(p)
    ps.sort_stats('time').print_stats(10)

def evaluate():
    if os.environ.get('FLASK_ENV') == 'TESTING':
        logger.info('Preparing evaluation database...')
        db.create_all()

        evaluate_clustering()

        logger.info('Cleaning up evaluation database...')
        db.session.remove()
        db.drop_all()
    else:
        logger.error('This function must be run with FLASK_ENV=TESTING.')
