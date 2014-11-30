import os
from difflib import SequenceMatcher
from datetime import datetime

import numpy as np
from scipy.sparse import csr_matrix, hstack
from sklearn.preprocessing import normalize
from galaxy import vectorize, concept_vectorize
from galaxy.cluster.ihac import Hierarchy

from argos.conf import APP
from argos.datastore import db
from argos.core.models import Event, Article
conf = APP['CLUSTERING']

def load_hierarchy():
    global h
    PATH = conf['hierarchy_path']
    if os.path.exists(PATH):
        h = Hierarchy.load(PATH)
    else:
        h = Hierarchy(metric=conf['metric'],
                      lower_limit_scale=conf['lower_limit_scale'],
                      upper_limit_scale=conf['upper_limit_scale'])
load_hierarchy()

def cluster(new_articles, min_articles=3):
    """
    Clusters a list of Articles into Events.

    The `min_articles` param specifies the minimum amount of member articles required
    to create or preserve an event. If an existing event comes to have less than this
    minimum, it is deleted.
    """
    # Build the article vectors.
    vecs = build_vectors(new_articles, conf['weights'])

    # Fit the article vecs into the hierarchy.
    node_ids = h.fit(vecs)

    # Match the articles with their node ids.
    for i, a in enumerate(new_articles):
        a.node_id = int(node_ids[i])
    db.session.commit()

    # Get the (event) clusters.
    clusters = h.clusters(distance_threshold=conf['threshold'], with_labels=False)

    # Filter out events that do not meet the minimum articles requirement.
    clusters = [clus for clus in clusters if len(clus) >= min_articles]

    process_events(clusters)

    h.save(os.path.expanduser(conf['hierarchy_path']))

def process_events(clusters):
    """
    Takes clusters of node uuids and
    builds, modifies, and deletes events out of them.
    """
    now = datetime.utcnow()

    # Get existing event clusters.
    event_map = {}
    existing  = {}
    for e in Event.all_active():
        event_map[e.id] = e
        existing[e.id]  = [a.node_id for a in e.articles]

    # Figure out which events to update, delete, and create.
    to_update, to_create, to_delete, unchanged = triage(existing, clusters)

    for a_ids in to_create:
        articles = [Article.query.filter_by(node_id=id.item()).first() for id in a_ids]
        e = Event(articles)
        db.session.add(e)

    for e_id, a_ids in to_update.items():
        e = event_map[e_id]
        articles = [Article.query.filter_by(node_id=id.item()).first() for id in a_ids]
        e.members = articles
        e.update()

    # Freeze expiring events and clean up their articles from the hierarchy.
    for e_id in unchanged:
        e = event_map[e_id]
        if (now - e.updated_at).days > 3:
            e.active = False
            nodes = [h.to_iid(a.node_id) for a in e.articles]
            h.prune(nodes)

    # Do this LAST so any of this event's associated articles
    # have a chance to be moved to their new clusters (if any).
    for e_id in to_delete:
        db.session.delete(event_map[e_id])
        # does this need to prune the articles as well?
        # i think the assumption is that a deleted event's articles have all migrated elsewhere.

    db.session.commit()

def triage(existing, new):
    """
    Args:

        existing => {event_id => [article_ids], ...}
        new      => [[article_ids], ...]

    Returns which _existing_ clusters have been _updated_,
    which ones should be _created_,
    which ones should be _deleted_,
    and which ones are _unchanged_.

    Each group is in a different format.

    to_update => {event_id => [article_ids], ...}
    to_create => [[article_ids], ...]
    to_delete => [event_id, ...]
    unchanged => [event_id, ...]
    """
    to_update = {}
    to_delete = []
    unchanged = []

    # Keep sorting consistent.
    new_clusters = [sorted(clus) for clus in new]

    # For each existing cluster,
    for id, clus in existing.items():
        # Keep sorting consistent.
        clus = sorted(clus)
        s = SequenceMatcher(a=clus)

        # Compare to each remaining new cluster...
        candidates = []
        for i, new_clus in enumerate(new_clusters):
            s.set_seq2(new_clus)
            r = s.ratio()

            # If the similarity is 100%, then the cluster is unchanged.
            if r == 1.:
                unchanged.append(id)
                new_clusters.pop(i)
                break

            # If the similarity is over 50%, consider the new
            # cluster as a candidate for the old cluster.
            elif r >= 0.5:
                candidates.append({'ratio': r, 'idx': i})

        else:
            # If we have candidates, get the most similar one.
            if candidates:
                candidates = sorted(candidates, key=lambda x: x['ratio'], reverse=True)
                top = candidates[0]['idx']

                # This new cluster is now claimed,
                # remove it from the new clusters.
                to_update[id] = new_clusters.pop(top)

            # If there were no matches for the old cluster,
            # delete it.
            else:
                to_delete.append(id)

    # Any remaining new_clusters are considered new, independent clusters.
    to_create = new_clusters

    return to_update, to_create, to_delete, unchanged


def build_vectors(articles, weights):
    """
    Build weighted vector representations for a list of articles.
    """
    pub_vecs, bow_vecs, con_vecs = [], [], []
    for a in articles:
        pub_vecs.append(np.array([a.published]))
        bow_vecs.append(vectorize(a.text))
        con_vecs.append(concept_vectorize([c.slug for c in a.concepts]))

    pub_vecs = normalize(csr_matrix(pub_vecs), copy=False)
    bow_vecs = normalize(csr_matrix(bow_vecs), copy=False)
    con_vecs = normalize(csr_matrix(con_vecs), copy=False)

    # Merge vectors.
    vecs = hstack([pub_vecs, bow_vecs, con_vecs])

    # Convert to a scipy.sparse.lil_matrix because it is subscriptable.
    vecs = vecs.tolil()

    # Apply weights to the proper columns:
    # col 0 = pub, cols 1-101 = bow, 102+ = concepts
    # weights = [pub, bow, concept]
    vecs[:,0]     *= weights[0]
    vecs[:,1:101] *= weights[1]
    vecs[:,101:]  *= weights[2]

    return vecs.toarray()
