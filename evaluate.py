import os
import cProfile, pstats
from brain import cluster

# Logging.
from logger import logger
logger = logger(__name__)

cluster.DATABASE = 'evaluate'

def evaluate_clustering():
    """
    Evaluate the clustering algorithm.
    """

    logger.info('Emptying evaluation database...')
    cluster.database().empty()

    logger.info('Constructing expected clusters and articles...')
    expected_clusters = {}
    articles = []
    for dir, subdir, files in os.walk('resources/cluster_evaluation/organized_articles'):
        for file in files:
            filepath = os.path.join(dir, file)
            name, ext = os.path.splitext(filepath)
            if ext == '.txt':
                category = dir.split('/')[-1]
                f = open(filepath, 'r')
                article = {
                    'text': f.read(),
                    'title': name.split('/')[-1]
                }
                expected_clusters.setdefault(category, []).append(article)
                articles.append(article)

    logger.info('Will cluster %s articles.' % len(articles))
    logger.info('Expecting %s clusters.' % len(expected_clusters.keys()))

    logger.info('Clustering...')
    p = cProfile.Profile()
    #clusters = cluster.cluster(articles, debug=True, threshold=0.04)
    clusters = p.runcall(cluster.cluster, articles, debug=True, threshold=0.04)

    logger.info('Created %s clusters.' % len(clusters))

    logger.info('Cluster composition is as follows...')
    for c in clusters:
        logger.info([m['title'] for m in c.members])

    logger.info('Profiling statistics from the clustering...')
    ps = pstats.Stats(p)
    ps.sort_stats('time').print_stats(10)

def main():
    evaluate_clustering()


if __name__ == '__main__':
    main()
