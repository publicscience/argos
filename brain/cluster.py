"""
Cluster
==============

Clusters text documents.

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
        candidate_clusters = [c for c in active_clusters if set(ents).intersection(c.features)]

        # Keep tracking of qualifying clusters
        # and their avg sim with this article.
        # [(cluster, avg_sim),...]
        qualifying_clusters = []

        # Compare the article with the candidate clusters.
        for cluster in candidate_clusters:
            avg_sim = cluster.similarity_with_vector(vector)
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
            active_clusters.append( Cluster({'members': [article]}) )

    for cluster in active_clusters:
        # Mark expired clusters inactive.
        if (now - cluster.updated_at).days > 3:
            cluster.active = False
        else:
            cluster.update(save=False)
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
    A cluster.
    """
    def __init__(self, data={}):
        """
        Initialize the cluster with some data.

        Args:
            | data (dict)   -- optional, the data to initialize the cluster with.

        Cluster data looks like::

            {
                'id': *,
                'title': str,
                'members': list,
                'features': list,
                'active': bool,
                'summary' : str,
                'updated_at': datetime,
                'created_at': datetime
            }
        """
        # Defaults
        self.defaults = {
            'active': True,
            'title': '',
            'members': [],
            'features': [],
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
        """
        Generate a summary for this cluster.
        """
        # something like:
        # self.summary = summarize([m['text'] for m in self.members])
        pass

    def titleize(self):
        """
        Generate a title for this cluster.

        Looks for the cluster member that is most similar to the others,
        and then uses the title of that member.
        """
        max_member = (None, 0)
        for member in self.members:
            v = self.vectorize_member(member)
            avg_sim = self.similarity_with_vector(v)
            if avg_sim > max_member[1]:
                max_member = (member, avg_sim)
        self.title = max_member[0]['title']

    def featurize(self):
        """
        Update (weighted) features for this cluster.

        In this implemention, entities = features.
        """
        self.features = entities([m['text'] for m in self.members])

    def update(self, save=True):
        """
        Update the cluster's attributes,
        optionally saving (saves by default).
        """
        self.titleize()
        self.summarize()
        self.featurize()

        if save:
            self.save()

    def save(self):
        """
        Persist the cluster's data to the database.
        """
        db = database()

        # Assemble the data to save.
        keys = self.defaults.keys()
        data = {key: getattr(self, key) for key in keys}

        # If there's an id, include that as well.
        if hasattr(self, '_id'):
            data['_id'] = getattr(self, '_id')

        # Set the id from the saved record.
        self._id = db.save(data)

    def add(self, member):
        """
        Add an member to the cluster.
        """
        self.members.append(member)

    def vectorize_member(self, member):
        """
        Vectorize/represent a cluster member.
        """
        return vectorize(member['text'])

    def vectorize_members(self):
        """
        Vectorize all members in a cluster
        into a 1D array.
        """
        return vectorize([m['text'] for m in self.members]).toarray().flatten()

    def similarity_with_vector(self, vector):
        """
        Calculate the similarity of this vector
        against each member of the cluster.
        """
        sims = []
        for member in self.members:
            v = self.vectorize_member(member)
            sims.append(1 - jaccard(vector, v))

        # Calculate average similarity.
        return sum(sims)/len(sims)

    def similarity_with_cluster(self, cluster):
        """
        Calculate the average similarity of each
        member to each member of the other cluster.
        """
        avg_sims = []
        vs = self.vectorize_members()
        vs_ = cluster.vectorize_members()
        return 1 - jaccard(vs, vs_)

def evaluate():
    """
    Evaluate the clustering algorithm.
    """
    pass
