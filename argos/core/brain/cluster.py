"""
Cluster
==============

Clusters text documents.
"""

from collections import namedtuple

Score = namedtuple('Score', ['cluster', 'avg_sim'])

def cluster(obj, clusters, threshold=0.7, logger=None):
    """
    A generic clustering function.

    It relies on the :class:`Clusterable` object's similarity function to assign
    the object to a cluster, if a qualifying one is found.

    .. note::
        This function *does not* create a new cluster if a qualifying one isn't found.

        Nor does it save the cluster changes – it is expected that the database session is committed outside of the function.

    Args:
        | obj (Clusterable)     -- the object to be clustered
        | cluster (list)        -- the list of Clusters to compare to
        | threshold (float)     -- the minimum similarity threshold for a qualifying cluster
        | logger (logger)       -- will log to this logger if one is provided (default: None)

    Returns:
        | the qualifying cluster if found, else None.

    It's meant to be called from :class:`Cluster` subclass's own `cluster` methods.
    """

    # For logging purposes.
    name = obj.__class__.__name__
    logger.debug('Using {0} candidate clusters.'.format(len(clusters)))

    # Keep tracking of qualifying clusters
    # and their avg sim with this obj.
    qual_scores = []

    # The selected cluster
    # to return.
    sel_clus = None

    # Compare the obj with the candidate clusters.
    for clus in clusters:
        avg_sim = clus.similarity(obj)
        if logger: logger.debug('Average similarity was {0}.'.format(avg_sim))
        if avg_sim > threshold:
            qual_scores.append( Score(clus, avg_sim) )

    num_qual = len(qual_scores)
    if logger: logger.debug('Found {0} qualifying clusters.'.format(num_qual))

    if num_qual == 1:
        # Grab the only cluster and add the obj.
        if logger: logger.debug('Only one qualifying cluster, adding {0} to it.'.format(name))
        sel_clus = qual_scores[0].cluster

    elif num_qual > 1:
        # Get the most similar cluster and add the obj.
        if logger: logger.debug('Multiple qualifying clusters found, adding {0} to the most similar one.'.format(name))
        max_score = Score(None, 0)
        for score in qual_scores:
            if score.avg_sim > max_score.avg_sim:
                max_score = score
        sel_clus = max_score.cluster

    if sel_clus:
        sel_clus.add(obj)

    return sel_clus
