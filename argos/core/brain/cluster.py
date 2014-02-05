"""
Cluster
==============

Clusters text documents.
"""

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
    # [(cluster, avg_sim),...]
    qualifying_clusters = []
    selected_cluster = None

    # Compare the obj with the candidate clusters.
    for cluster in clusters:
        avg_sim = cluster.similarity(obj)
        if logger: logger.debug('Average similarity was {0}.'.format(avg_sim))
        if avg_sim > threshold:
            qualifying_clusters.append((cluster, avg_sim))

    num_qualified = len(qualifying_clusters)
    if logger: logger.debug('Found {0} qualifying clusters.'.format(num_qualified))

    if num_qualified == 1:
        # Grab the only cluster and add the obj.
        if logger: logger.debug('Only one qualifying cluster, adding {0} to it.'.format(name))
        selected_cluster = qualifying_clusters[0][0]

    elif num_qualified > 1:
        # Get the most similar cluster and add the obj.
        if logger: logger.debug('Multiple qualifying clusters found, adding {0} to the most similar one.'.format(name))
        max_cluster = (None, 0)
        for cluster in qualifying_clusters:
            if cluster[1] > max_cluster[1]:
                max_cluster = cluster
        selected_cluster = max_cluster[0]

    if selected_cluster:
        selected_cluster.add(obj)

    return selected_cluster
