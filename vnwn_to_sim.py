"""
Takes ./parsed/vnwn.json and creates a pairwise similarity matrix for the verbs
with corresponding synsets in wn.

Tries two ways to get synsets:
    1. The first one in vnwn.json
    2. Querying verbnet for synsets

TODO:
    How to deal with verbs without synsets?
    If clustering on subset in WordNet, we might need to cluster on a subset in
    VerbNet as well..
    Or maybe grab a synset from a similar WordNet class? That's probably not
    good...
"""

import nltk
from nltk.corpus import wordnet as wn
from vnutil import load_json, save_list
from parse_verbnet import VN_WN_MAP_FNAME
from vnerrors import correct_wn_synset
from scipy.spatial.distance import pdist
import numpy as np


# For choosing similarity function, see "A Review of Semantic Similarity
# Measures in WordNet"
# http://www.cartagena99.com/recursos/alumnos/ejercicios/Article%201.pdf

# Path-based:
#     Standard path_similarity, probably
#     or wu-palmer since Martha Palmer
# information-content:
#     Need to download IC corpus, but might be more sophisticated
#     Disadv: limited vocab
#     Use resnik similarity, probably

SIMILARITY_FUNC = wn.wup_similarity


def wnsim(a, b):
    """
    2-ary similarity function wrapper that accepts the format of elements in
    `members`
    """
    # Assuming format [verb, vnclass, ss]
    return SIMILARITY_FUNC(a[2], b[2])


if __name__ == '__main__':
    # Update wordnet
    nltk.download('wordnet')

    members = []

    num_no_synsets = 0
    num_wn_synsets = 0

    vnwn = load_json(VN_WN_MAP_FNAME)
    print "Getting synsets"
    for vnmember, synsets in vnwn.iteritems():
        # Default choose primary synset.
        verb, vnclass = vnmember.split('#')
        if not synsets:
            # Then try to get a synset from wn
            wn_synsets = wn.synsets(verb, pos='v')
            if wn_synsets:
                ss = wn_synsets[0]
                num_wn_synsets += 1
            else:
                num_no_synsets += 1
                ss = None
        else:
            # Synsets are encoded according to "sense key encoding"
            # here, but without head_word and head_id, so we add two ::s to
            # satisfy nltk
            # https://wordnet.princeton.edu/man/senseidx.5WN.html#toc3
            ss_raw = correct_wn_synset(synsets[0])
            # Design choice to use SYNSETS instead of LEMMAs (check into this
            # later)
            ss = wn.lemma_from_key('{}::'.format(ss_raw)).synset()
        if ss:
            members.append([verb, vnclass, ss])

    # Now construct distance matrix
    print "Constructing distance matrix"
    distmat = np.empty((len(members), len(members), ))
    distmat[:] = np.NaN
    for i, a in enumerate(members):
        print i
        for j, b in enumerate(members):
            # Don't compute if the other side of this matrix has already been
            # computed
            if not np.isnan(distmat[j, i]):
                distmat[i, j] = distmat[j, i]
            else:
                distmat[i, j] = wnsim(a, b)

    print distmat
    np.savetxt('../BigData/parsed/wn-distmat.csv', distmat,
               fmt='%f', delimiter=',')
    save_list(
        map(lambda x: '{}#{}'.format(x[0], x[1]), members),
        '../BigData/parsed/wn-members.txt'
    )
    save_list(
        map(lambda x: x[2].name(), members),
        '../BigData/parsed/wn-synsets.txt'
    )
