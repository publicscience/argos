"""
Cluster
==============

Clusters text documents.

A cluster looks like::

    {
        'id': *,
        'title': str,
        'articles': list,
        'entities': list,
        'active': bool,
        'summary' : str,
        'updated_at': datetime,
        'created_at': datetime
    }
"""

from brain import vectorize, entities
from adipose import Adipose
from scipy.spatial.distance import jaccard
from datetime import datetime

DATABASE = 'brain'
COLLECTION = 'clusters'

def cluster(articles, threshold=0.7):
    """
    Clusters a set of articles
    into existing clusters.

    Args:
        | articles (list)   -- the articles to classify (a list of article dicts)
        | threshold (float) -- the similarity threshold for qualifying a cluster
    """

    active_clusters = clusters()
    now = datetime.utcnow()

    # TO DO: BIAS CLOSER PUBLICATION DATES
    for article in articles:
        text = article['text']

        # Build bag-of-words vector representation.
        vector = vectorize(text)

        # Extract entities as another representation.
        ents_w_weights = entities(text)
        ents = [e[0] for e in ents_w_weights]

        # Select candidate clusters,
        # i.e. active clusters which share at least one entity with this article.
        candidate_clusters = [c for c in active_clusters if set(ents).intersection(c.entities)]

        # Keep tracking of qualifying clusters
        # and their avg sim with this article.
        # [(cluster, avg_sim),...]
        qualifying_clusters = []

        # Compare the article with the candidate clusters.
        for cluster in candidate_clusters:
            avg_sim = cluster.similarity(vector)
            if avg_sim > threshold:
                qualifying_clusters.append((cluster, avg_sim))

        num_qualified = len(qualifying_clusters)

        if num_qualified == 1:
            # Grab the only cluster and add the article.
            qualifying_clusters[0][0].add(article)

        elif num_qualified > 1:
            # Get the most similar cluster and add the article.
            max_cluster = (None, 0)
            for cluster in qualifying_clusters:
                if cluster[1] > max_cluster[1]:
                    max_cluster = cluster
            max_cluster[0].add(article)

        else:
            # Create a new cluster.
            active_clusters.append( Cluster({'articles': [article]}) )

    for cluster in active_clusters:
        # Mark expired clusters inactive.
        if (now - cluster.updated_at).days > 3:
            cluster.active = False
        else:
            cluster.update()
        cluster.save()


def clusters(active=True):
    """
    Fetch cluster data and
    create Clusters.
    """
    db = database()
    return [Cluster(c) for c in db.find({'active': active})]


def database():
    return Adipose(DATABASE, COLLECTION)


class Cluster():
    """
    TO DO WRITE THIS
    """
    def __init__(self, data={}):
        # Defaults
        self.defaults = {
            'active': True,
            'title': '',
            'articles': [],
            'entities': [],
            'summary': '',
            'created_at': datetime.utcnow(),
            'updated_at': datetime.utcnow()
        }
        for key in self.defaults:
            setattr(self, key, self.defaults[key])

        # Overwrite defaults with passed values.
        for key in data:
            setattr(self, key, data[key])

    def summarize(self):
        pass

    def titleize(self):
        pass

    def entitize(self):
        pass

    def update(self):
        self.titleize()
        self.summarize()
        self.entitize()

    def save(self):
        db = database()

        # Assemble the data to save.
        keys = self.defaults.keys()
        data = {key: getattr(self, key) for key in keys}

        # If there's an id, include that as well.
        if hasattr(self, '_id'):
            data['_id'] = getattr(self, '_id')

        # Set the id from the saved record.
        self._id = db.save(data)

    def add(self, article):
        self.articles.append(article)

    def similarity(self, vector):
        sims = []
        # Calculate the similarity of this article
        # against each article in the cluster.
        for article in self.articles:
            vector_ = vectorize(article['text'])
            sims.append(1 - jaccard(vector, vector_))

        # Calculate average similarity.
        return sum(sims)/len(sims)

