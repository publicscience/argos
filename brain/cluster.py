"""
Cluster
==============

Clusters text documents.

"""

from brain import vectorize, entities
from adipose import Adipose
from scipy.spatial.distance import jaccard
from datetime import datetime

from numpy import ndarray

# Logging.
from logger import logger

DATABASE = 'brain'
COLLECTION = 'clusters'

def cluster(articles, threshold=0.7, debug=False):
    """
    Clusters a set of articles
    into existing clusters.

    Args:
        | articles (list)   -- the articles to classify (a list of article dicts)
        | threshold (float) -- the similarity threshold for qualifying a cluster
    """

    log = logger('clustering')
    if debug:
        log.setLevel('DEBUG')
    else:
        log.setLevel('ERROR')

    log.debug('Threshold is set to %s.' % threshold)

    active_clusters = clusters()

    now = datetime.utcnow()

    # TO DO: BIAS CLOSER PUBLICATION DATES
    for article in articles:
        log.debug('There are %s active clusters.' % len(active_clusters))
        text = article['text']

        # Extract entities to use as another representation.
        ents = entities(text)
        log.debug('Found %s entities.' % len(ents))

        # Build bag-of-words vector representation.
        article['vector'] = [vectorize(text), vectorize(' '.join(ents))]

        # Select candidate clusters,
        # i.e. active clusters which share at least one entity with this article.
        candidate_clusters = [c for c in active_clusters if set(ents).intersection(c.features)]
        log.debug('Found %s candidate clusters.' % len(candidate_clusters))

        # Keep tracking of qualifying clusters
        # and their avg sim with this article.
        # [(cluster, avg_sim),...]
        qualifying_clusters = []

        # Compare the article with the candidate clusters.
        for cluster in candidate_clusters:
            avg_sim = cluster.similarity_with_object(article)
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
            new_cluster = Cluster({'members': [article]})
            new_cluster.update(save=False)
            active_clusters.append(new_cluster)

    for cluster in active_clusters:
        # Mark expired clusters inactive.
        if (now - cluster.updated_at).days > 3:
            cluster.active = False
        else:
            cluster.update(save=False)
        cluster.save()

    return active_clusters


def clusters(active=True):
    """
    Fetch cluster data and
    create Clusters.
    """
    db = database()
    return [Cluster(c) for c in db.all({'active': active})]


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

        # Need to handle pickled vector data specially.
        # Looking for a better way!
        for member in self.members:
            unpickled_vecs = []
            for vec in member.get('vector', []):
                if type(vec) is not ndarray:
                    vec = unpickle(vec)
                unpickled_vecs.append(vec)
            member['vector'] = unpickled_vecs

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
            avg_sim = self.similarity_with_object(member)
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

        # Need to handle member vector data properly.
        # Ideally this is only a temporary solution;
        # I imagine there are better approaches.
        for member in data['members']:
            pickled_vecs = []
            for vec in member.get('vector', []):
                pickled_vecs.append(db.pickle(vec))
            member['vector'] = pickled_vecs

        # Set the id from the saved record.
        self._id = db.save(data)

    def add(self, member):
        """
        Add an member to the cluster.
        """
        self.members.append(member)

    def similarity_with_object(self, obj):
        """
        Calculate the similarity of this object
        against each member of the cluster.
        """
        sims = []
        for member in self.members:
            v_m = self._vectorize_member(member)
            v_o = self._vectorize_member(obj)

            # Linearly combine the similarity values,
            # weighing them according to these coefficients.
            coefs = [2, 1]
            sim = 0
            for i, v in enumerate(v_m):
                s = 1 - jaccard(v_o[i], v_m[i])
                sim += (coefs[i] * s)

            # Normalize back to [0, 1] and save.
            sim = sim/sum(coefs)
            sims.append(sim)

        # Calculate average similarity.
        return sum(sims)/len(sims)

    def similarity_with_cluster(self, cluster):
        """
        Calculate the average similarity of each
        member to each member of the other cluster.
        """
        avg_sims = []
        vs = self._vectorize_members()
        vs_ = cluster._vectorize_members()
        return 1 - jaccard(vs, vs_)

    def _vectorize_member(self, member):
        """
        Vectorize/represent a cluster member.
        Caches vectors on the member.

        May return a list of vectors if multiple
        vector representations are used.
        """
        if not member.get('vector'):
            # Members are represented both by a:
            # – bag of words vector
            # – entities vector
            bow_vec = vectorize(member['text'])
            ent_vec = vectorize(' '.join(entities(member['text'])))
            member['vector'] = [bow_vec, ent_vec]
        return member['vector']

    def _vectorize_members(self):
        """
        Vectorize all members in a cluster
        into a 1D array.
        """
        return vectorize([m['text'] for m in self.members]).toarray().flatten()
