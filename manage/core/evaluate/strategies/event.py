"""
Article similarity patches
==========================
Any methods you define here which include
'similarity' in their name will be
used as alternative similarity methods
for evaluating article similarity.
"""

from argos.core.models import Article

from scipy.spatial.distance import jaccard
from math import isnan

def simple_similarity(self, obj, weights):
    return 1.0

def only_entity_similarity(self, obj, weights):
    v = self.vectorize()
    v_ = obj.vectorize()

    # Vectors are [bow_vec, ent_vec]
    dist = jaccard(v_[1], v[1])

    # If no distance, just consider them completely different.
    if isnan(dist):
        dist = 1

    return 1 - dist

def only_word_similarity(self, obj, weights):
    v = self.vectorize()
    v_ = obj.vectorize()

    # Vectors are [bow_vec, ent_vec]
    dist = jaccard(v_[0], v[0])

    # If no distance, just consider them completely different.
    if isnan(dist):
        dist = 1

    return 1 - dist

def entity_and_word_average_similarity(self, obj, weights):
    v = self.vectorize()
    v_ = obj.vectorize()

    # Vectors are [bow_vec, ent_vec]
    dist_bow = jaccard(v_[0], v[0])
    dist_ent = jaccard(v_[1], v[1])

    # If no distance, just consider them completely different.
    if isnan(dist_bow):
        dist_bow = 1
    if isnan(dist_ent):
        dist_ent = 1

    return 1 - (dist_bow + dist_ent)/2

def entity_and_word_similarity(self, obj, weights):
    # Vectors are [bow_vec, ent_vec]
    v = self.vectorize()
    v_ = obj.vectorize()

    sim = 0
    for idx, dist in enumerate(v):
        dist = jaccard(v_[idx], v[idx])
        if isnan(dist):
            dist = 1
        s = 1 - dist
        sim += weights[idx] * s

    return sim/sum(weights)
