"""
Cluster
==============

Clusters text documents.
"""

from app import db
from brain import vectorize, entities
from models import Cluster
from scipy.spatial.distance import jaccard
from datetime import datetime

# Logging.
from logger import logger

def cluster(articles, threshold=0.7, tag='', debug=False):
    """
    Clusters a set of articles
    into existing clusters.

    Args:
        | articles (list)   -- the articles to classify (a list of article dicts)
        | threshold (float) -- the similarity threshold for qualifying a cluster
        | tag (str)         -- the tag of the clusters to look through
    """

    log = logger('clustering')
    if debug:
        log.setLevel('DEBUG')
    else:
        log.setLevel('ERROR')

    log.debug('Threshold is set to %s.' % threshold)

    active_clusters = Cluster.query.filter_by(active=True, tag=tag).all()

    now = datetime.utcnow()

    # TO DO: BIAS CLOSER PUBLICATION DATES
    for article in articles:
        log.debug('There are %s active clusters.' % len(active_clusters))

        # Select candidate clusters,
        # i.e. active clusters which share at least one entity with this article.
        a_ents = [entity.id for entity in article.entities]
        candidate_clusters = []
        for c in active_clusters:
            c_ents = [entity.id for entity in c.entities]
            if set(c_ents).intersection(a_ents):
                candidate_clusters.append(c)
        log.debug('Found %s candidate clusters.' % len(candidate_clusters))

        # Keep tracking of qualifying clusters
        # and their avg sim with this article.
        # [(cluster, avg_sim),...]
        qualifying_clusters = []

        # Compare the article with the candidate clusters.
        for cluster in candidate_clusters:
            avg_sim = cluster.similarity(article)
            log.debug('Average similarity was %s.' % avg_sim)
            if avg_sim > threshold:
                qualifying_clusters.append((cluster, avg_sim))

        num_qualified = len(qualifying_clusters)
        log.debug('Found %s qualifying clusters.' % num_qualified)

        if num_qualified == 1:
            # Grab the only cluster and add the article.
            log.debug('Only one qualifying cluster, adding article to it.')
            qualifying_clusters[0][0].add(article)

        elif num_qualified > 1:
            # Get the most similar cluster and add the article.
            log.debug('Multiple qualifying clusters found, adding article to the most similar one.')
            max_cluster = (None, 0)
            for cluster in qualifying_clusters:
                if cluster[1] > max_cluster[1]:
                    max_cluster = cluster
            max_cluster[0].add(article)

        else:
            # Create a new cluster.
            log.debug('No qualifying clusters found, creating a new cluster.')
            new_cluster = Cluster([article], tag=tag)
            db.session.add(new_cluster)
            active_clusters.append(new_cluster)

    for cluster in active_clusters:
        # Mark expired clusters inactive.
        if (now - cluster.updated_at).days > 3:
            cluster.active = False
        else:
            cluster.update()
    db.session.commit()

    return active_clusters

