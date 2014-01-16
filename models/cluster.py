from app import db
from brain import vectorize, entities
from scipy.spatial.distance import jaccard
from datetime import datetime

class Cluster(db.Model):
    """
    A cluster.
    """
    id = db.Column(db.Integer, primary_key=True)
    active = db.Column(db.Boolean, default=True)
    members = db.relationship('Article', backref='cluster', lazy='select')
    features = db.Column(db.PickleType)
    title = db.Column(db.Unicode)
    summary = db.Column(db.UnicodeText)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow)

    def __init__(self, members):
        """
        Initialize a cluster with some members.
        """
        self.members = members
        self.update()

    def summarize(self):
        """
        Generate a summary for this cluster.
        """
        # something like:
        # self.summary = summarize([m.text for m in self.members])
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
        self.title = max_member[0].title

    def featurize(self):
        """
        Update (weighted) feature vector for this cluster.

        In this implemention, entities = features.
        """
        self.features = vectorize(' '.join(entities([m.text for m in self.members])))

    def feature_overlap(self, article):
        #a_ents = article.vectorize()[1]
        pass

    def update(self):
        """
        Update the cluster's attributes,
        optionally saving (saves by default).
        """
        self.titleize()
        self.summarize()
        self.featurize()
        self.updated_at = datetime.utcnow()
        self.created_at = datetime.utcnow()

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
            v_m = member.vectorize()
            v_o = obj.vectorize()

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
        vs = self.vectorize()
        vs_ = cluster.vectorize()
        return 1 - jaccard(vs, vs_)

    def vectorize(self):
        """
        Vectorize all members in a cluster
        into a 1D array.
        """
        return vectorize([m.text for m in self.members]).toarray().flatten()
