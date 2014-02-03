"""
Summarize
==============

Summarizes documents.

Currently uses a modified version of PyTeaser:
    https://github.com/xiaoxu193/PyTeaser
Which is based off of TextTeaser:
    https://github.com/MojoJolo/textteaser

This currently only supports single document summarization.
"""

from argos.core.brain import tokenize, sentences, stopwords, vectorize
from argos.core.models import Article

from re import sub
from math import fabs
from collections import Counter
from scipy.spatial.distance import cosine

IDEAL_WORDS = 20

def summarize(title, text, summary_length=5):
    """
    Summarizes a single document.
    """
    summary = []
    keys = keywords(text)
    title_tokens = tokenize(title)

    # Score sentences and use the top selections.
    ranks = score(sentences(text), title_tokens, keys).most_common(summary_length)
    for rank in ranks:
        summary.append(rank[0])

    return summary


def multisummarize(docs, summary_length=5):
    """
    Summarize multi documents.

    The current implementation is super naive,
    thus the quality and coherence of its summaries is pretty damn terrible.
    But it's purpose for now is that there is *some* API for
    multidoc summarization.

    btw: this is super slow. takes well over a minute for 4 moderately-sized documents.
    """
    # Collect all sentences from the input documents.
    # Also collect position information about each sentence.
    sents = []
    for doc in docs:
        sents += [(sent, vectorize(sent), pos + 1) for pos, sent in enumerate(sentences(doc))]
    clusters = []

    # Cluster the sentences.
    for sent in sents:
        # sent = (sent, vec, pos)

        # Keep track of the maximum scoring cluster
        # (above some minimum similarity)
        # and the avg sim score.
        min_sim = 0.01
        max_cluster = None, min_sim
        for cluster in clusters:
            avg_sim = 0
            for sent_c in cluster:
                avg_sim += (1 - cosine(sent[1], sent_c[1]))
            avg_sim = avg_sim/len(cluster)
            if avg_sim >= max_cluster[1]:
                max_cluster = cluster, avg_sim

        # If a cluster was found, 
        # add the sentence to it
        if max_cluster[0]:
            max_cluster[0].append(sent)

        # Otherwise, create a new cluster.
        else:
            clusters.append([sent])

    # Rank the clusters.
    # Assuming that clusters with more sentences are more important,
    # take the top 5.
    ranked_clusters = sorted(clusters, key=lambda x: -len(x))[:summary_length]

    # For each sentence cluster, select the highest scoring sentence.
    # Again - very naive.
    ideal_length = 20
    summary_sentences = []
    for cluster in ranked_clusters:
        max_sent = None, 0
        for sent in cluster:
            avg_sim = 0
            for sent_c in cluster:
                avg_sim += 1 - cosine(sent[1], sent_c[1])
            avg_sim = avg_sim/len(cluster)
            pos = sent[2]
            length = fabs(ideal_length - len(tokenize(sent[0])))/ideal_length

            # Score is the average similarity penalized by distance from ideal length,
            # weighted by the inverse of the position.
            score = (avg_sim - length)/pos
            if score >= max_sent[1]:
                max_sent = sent[0], score
        summary_sentences.append(max_sent[0])

    return summary_sentences



def score(sentences, title_words, keywords):
    """
    Score sentences based on their features.

    Args:
        | sentences (list)      -- list of sentences to score
        | title_words (list)    -- list of words in the title
        | keywords (list)       -- list of keywords from the document
    """
    num_sentences = len(sentences)
    ranks = Counter()
    for i, s in enumerate(sentences):
        sentence = tokenize(s)

        # Calculate features.
        title_score = score_title(title_words, sentence)
        s_length = sentence_length(sentence)
        s_position = sentence_position(i+1, num_sentences)
        sbs_feature = sbs(sentence, keywords)
        dbs_feature = dbs(sentence, keywords)
        frequency = (sbs_feature + dbs_feature) / 2.0 * 10.0

        # Weighted average of feature scores.
        total_score = (title_score*1.5 + frequency*2.0 +
                      s_length*1.0 + s_position*1.0) / 4.0
        ranks[s] = total_score
    return ranks


def sbs(words, keywords):
    score = 0.0
    if not words:
        return 0
    for word in words:
        if word in keywords:
            score += keywords[word]
    return (1.0 / fabs(len(words)) * score)/10.0


def dbs(words, keywords):
    if not words:
        return 0

    summ = 0
    first = []
    second = []

    for i, word in enumerate(words):
        if word in keywords:
            score = keywords[word]
            if first == []:
                first = [i, score]
            else:
                second = first
                first = [i, score]
                dif = first[0] - second[0]
                summ += (first[1]*second[1]) / (dif ** 2)

    # number of intersections
    k = len(set(keywords.keys()).intersection(set(words))) + 1
    return (1/(k*(k+1.0))*summ)


def keywords(text):
    """
    Gets the top 10 keywords and their frequency scores
    from a document.
    Sorts them in descending order by number of occurrences.
    """
    from operator import itemgetter  # for sorting

    text = sub(r'[^\w ]', '', text)  # strip special chars
    text_with_stops = [x.strip('.').lower() for x in text.split()]

    numWords = len(text_with_stops)
    text = tokenize(text)
    freq = Counter()
    for word in text:
        freq[word] += 1

    minSize = min(10, len(freq))
    keywords = tuple(freq.most_common(minSize))  # get first 10
    keywords = dict((x, y) for x, y in keywords)  # recreate a dict

    for k in keywords:
        articleScore = keywords[k]*1.0 / numWords
        keywords[k] = articleScore * 1.5 + 1

    keywords = sorted(iter(keywords.items()), key=itemgetter(1))
    keywords.reverse()
    return dict(keywords)


def sentence_length(sentence):
    """
    Scores a sentence based on its length.
    """
    return 1 - fabs(IDEAL_WORDS - len(sentence)) / IDEAL_WORDS


def score_title(title, sentence):
    """
    Scores a sentence by its similarity
    to the document title.
    """
    intersect = [word for word in sentence if word in title]
    return len(intersect)/len(title)


def sentence_position(i, size):
    """
    Scores a sentence based on its position
    in a document.
    """

    normalized = i*1.0 / size
    if normalized > 0 and normalized <= 0.1:
        return 0.17
    elif normalized > 0.1 and normalized <= 0.2:
        return 0.23
    elif normalized > 0.2 and normalized <= 0.3:
        return 0.14
    elif normalized > 0.3 and normalized <= 0.4:
        return 0.08
    elif normalized > 0.4 and normalized <= 0.5:
        return 0.05
    elif normalized > 0.5 and normalized <= 0.6:
        return 0.04
    elif normalized > 0.6 and normalized <= 0.7:
        return 0.06
    elif normalized > 0.7 and normalized <= 0.8:
        return 0.04
    elif normalized > 0.8 and normalized <= 0.9:
        return 0.04
    elif normalized > 0.9 and normalized <= 1.0:
        return 0.15
    else:
        return 0
