from argos.datastore import db, Model
from argos.core.brain.summarizer import summarize, multisummarize

from sqlalchemy.ext.declarative import declared_attr

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
        # Only show concepts which have a name (some are extracted but don't map to known entities, so are not given a name).
        return list(map(with_score, [assoc for assoc in self.concept_associations if assoc.concept.name is not None]))

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

class Cluster(Clusterable):
    """
    A cluster.

    A Cluster is capable of clustering Clusterables.

    Note: A Cluster itself is a Clusterable; i.e. clusters
    can cluster clusters :)
    """
    __abstract__ = True
    title       = db.Column(db.Unicode, default='')
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

    def conceptize(self):
        """
        Update concepts (and mentions) for this cluster and score them.
        """
        self.mentions = list(set(chain.from_iterable([member.mentions for member in self.members])))

        # Get all concept associations for this cluster's members.
        assocs = chain.from_iterable([member.concept_associations for member in self.members])

        # Group associations by their concept.
        # Since `groupby` only looks at adjacent elements,
        # we have to first sort the associations by their concepts' slugs.
        key_func = lambda assoc: assoc.concept.slug
        grouped_assocs = [list(g) for k, g in groupby(sorted(assocs, key=key_func), key_func)]

        # Calculate the raw scores of each concept.
        raw_scores = {}
        for assoc_group in grouped_assocs:
            # Each group points to the same concept, so just grab the first.
            concept = assoc_group[0].concept
            raw_scores[concept] = sum(assoc.score for assoc in assoc_group)
        total = sum(raw_scores.values())

        # Calculate the final scores and create the associations.
        assocs = []
        for concept, raw_score in raw_scores.items():
            score = (raw_score/total)/(concept.commonness + 1) # +1 to avoid division by zero
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

        self.summarize()
        self.conceptize()

    def add(self, member):
        """
        Add an member to the cluster.
        """
        self.members.append(member)

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
