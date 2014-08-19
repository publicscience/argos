from argos.datastore import db, Model
from argos.core.brain.summarizer import summarize, multisummarize

from sqlalchemy.ext.declarative import declared_attr

from scipy.spatial.distance import jaccard
from math import isnan

from datetime import datetime
from itertools import chain, groupby

class Clusterable(Model):
    """
    An abstract class for anything that can be clustered.
    """
    __abstract__ = True
    id          = db.Column(db.Integer, primary_key=True)
    created_at  = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at  = db.Column(db.DateTime, default=datetime.utcnow)

    @declared_attr
    def concept_associations(cls):
        """
        Build the concepts relationship from the
        subclass's `__concepts__` class attribute.

        This uses an Associated Object so we can
        keep track of an additional property: the
        importance score of a particular concept to a
        given clusterable. The clusterable's concepts are
        directly accessed through the `concepts` property.

        The association model should inherit from BaseConceptAssociation.

        Example::

            __concepts__ = {'association_model': ArticleConceptAssociation,
                            'backref_name': 'article'}
        """
        args = cls.__concepts__

        return db.relationship(args['association_model'],
                backref=db.backref(args['backref_name']),
                cascade='all, delete, delete-orphan',
                order_by=args['association_model'].score.desc())

    @property
    def concepts(self):
        """
        Returns this model's associated concepts,
        along with their importance scores for this
        particular model.

        Note that `concepts` is a readonly property.
        Adding more concepts requires the addition of
        new instances of this model's concept-association model.
        That is, concepts must be added with an importance score
        which is accomplished by using the concept-association model.
        """
        def with_score(assoc):
            assoc.concept.score = assoc.score
            return assoc.concept
        return list(map(with_score, self.concept_associations))

    @property
    def concept_slugs(self):
        return [c.slug for c in self.concepts]

    @declared_attr
    def mentions(cls):
        """
        Build the mentions attribute from the
        subclass's `__mentions__` class attribute.

        Example::

            __mentions__ = {'secondary': articles_mentions, 'backref_name': 'articles'}
        """
        args = cls.__mentions__

        return db.relationship('Alias',
                secondary=args['secondary'],
                backref=db.backref(args['backref_name']))

    def vectorize(self):
        raise NotImplementedError

    def similarity(self, obj, weights=[2,1,2]):
        """
        Calculate the similarity between this
        clusterable and another clusterable.

        As the `similarity` method on the Clusterable class,
        this method is intended for comparing similarity across *peers*,
        that is, other instances of the same class.

        The idea here is that two identical instances should have
        a similarity of 1.0.

        Assumes that a clusterable's vectors are composed of
        a text (bag of words) vector and a concepts vector.
        The construction of these vectors should be implemented in
        the `vectorize` method.
        """
        v = self.vectorize()
        v_ = obj.vectorize()

        # Linearly combine the similarity values,
        # weighing them according to these coefficients.
        # [text vector, concept vector, publication date]
        sim = 0
        for i, vec in enumerate(v):
            dist = jaccard(v_[i], v[i])

            # Two empty vectors returns a jaccard distance of NaN.
            # Set it to be 1, i.e. consider them completely different
            # (or, put more clearly, they have nothing in common)
            # FYI if jaccard runs on empty vectors, it will throw a warning.
            if isnan(dist):
                dist = 1
            s = 1 - dist
            sim += (weights[i] * s)

        # Also take publication dates into account.
        ideal_time = 259200 # 3 days, in seconds
        t, t_ = self.created_at, obj.created_at

        # Subtract the more recent time from the earlier time.
        time_diff = t - t_ if t > t_ else t_ - t
        time_diff = time_diff.total_seconds()

        # Score is normalized [0, 1], where 1 is within the ideal time,
        # and approaches 0 the longer the difference is from the ideal time.
        time_score = 1 if time_diff < ideal_time else ideal_time/time_diff
        sim += (weights[2] * time_score)

        # Normalize back to [0, 1].
        return sim/sum(weights)


class Cluster(Clusterable):
    """
    A cluster.

    A Cluster is capable of clustering Clusterables.

    Note: A Cluster itself is a Clusterable; i.e. clusters
    can cluster clusters :)
    """
    __abstract__ = True
    title       = db.Column(db.Unicode)
    summary     = db.Column(db.UnicodeText)
    image       = db.Column(db.String())

    def __str__(self):
        return self.title

    def __repr__(self):
        return self.title

    @declared_attr
    def members(cls):
        """
        Build the members attribute from the
        subclass's `__members__` class attribute.

        Example::

            __members__ = {'class_name': 'Article', 'secondary': events_articles, 'backref_name': 'events'}
        """
        args = cls.__members__

        return db.relationship(args['class_name'],
                secondary=args['secondary'],
                backref=db.backref(args['backref_name']),
                lazy='dynamic')

    @staticmethod
    def cluster(cls, clusterables):
        """
        The particular clustering method for this Cluster class.
        Must be implemented on subclasses, otherwise raises NotImplementedError.
        """
        raise NotImplementedError

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
        if len(self.members) == 1:
            member = self.members[0]
            self.summary = ' '.join(summarize(member.title, member.text))
        else:
            self.summary = ' '.join(multisummarize([m.text for m in self.members]))
        return self.summary

    def titleize(self):
        """
        Generate a title for this cluster.
        Also selects a representative image.

        Looks for the cluster member that is most similar to the others,
        and then uses the title of that member.
        """
        max_member = (None, 0)
        max_member_w_image = (None, 0)
        for member in self.members:
            avg_sim = self.similarity(member)
            if avg_sim >= max_member[1]:
                max_member = (member, avg_sim)
            if avg_sim >= max_member_w_image[1] and member.image is not None:
                max_member_w_image = (member, avg_sim)

        self.title = max_member[0].title

        if max_member_w_image[0] is not None:
            self.image = max_member_w_image[0].image

    def conceptize(self):
        """
        Update concepts (and mentions) for this cluster.
        """
        self.mentions = list(set(chain.from_iterable([member.mentions for member in self.members])))

        # Calculate importance scores for the members' concepts.
        assocs = chain.from_iterable([member.concept_associations for member in self.members])

        # Group associations by their concept.
        # Since `groupby` only looks at adjacent elements,
        # we have to first sort the associations by their concepts' slugs.
        key_func = lambda assoc: assoc.concept.slug
        grouped_assocs = [list(g) for k, g in groupby(sorted(assocs, key=key_func), key_func)]

        # Calculate the raw scores of each concept.
        raw_scores = {}
        for assoc_group in grouped_assocs:
            concept = assoc_group[0].concept
            raw_scores[concept] = sum(assoc.score for assoc in assoc_group) - concept.commonness
        total = sum(raw_scores.values())

        # Calculate the final scores and create the associations.
        assocs = []
        for concept, raw_score in raw_scores.items():
            score = raw_score/total
            assoc = self.__class__.__concepts__['association_model'](concept, score) # this is nuts
            assocs.append(assoc)
        self.concept_associations = assocs

    def update(self):
        """
        Update the cluster's attributes,
        optionally saving (saves by default).
        """
        self.updated_at = datetime.utcnow()
        self.created_at = datetime.utcnow()
        self.titleize()
        self.summarize()
        self.conceptize()

    def add(self, member):
        """
        Add an member to the cluster.
        """
        self.members.append(member)

    def similarity(self, obj):
        """
        Because a Cluster is both a Clusterable and can have members,
        this similarity method will use the *peer* similarity method
        as defined in the Clusterable class if `obj` is an instance of the same class.
        In this case, the similarity should be 1.0 if the clusters are identical in composition;
        that is, they each have the same set of members. The members do not need to all be identical.

        Otherwise, it will treat obj as a potential member (i.e. a child)
        and handle similarity accordingly. In this case, `obj` must have a `similarity`
        method implemented. In this case, the similarity should be 1.0 if the candidate member (`obj`)
        is identical to *each* member of the Cluster (that is, all members are also identical to each other).
        """
        if self.__class__ == obj.__class__:
            return super().similarity(obj)
        else:
            sims = [obj.similarity(member) for member in self.members]

            # Calculate average similarity.
            return sum(sims)/len(sims)

    def timespan(self, start, end=None):
        """
        Get cluster members within a certain (date)timespan.

        Args:
            | start (datetime)
            | end (datetime)    -- default is now (UTC)
        """
        if end is None:
            end = datetime.utcnow()
        return [member for member in self.members if start < member.created_at < end]
