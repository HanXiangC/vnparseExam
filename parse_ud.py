"""
Parse the CoNLL-U format Universal Dependencies English corpus into a set of
natural, lemmatized and tokenized natural language sentences suitable for
input into word embedding models.

Format at http://universaldependencies.org/docs/format.html
"""

UD_FILES = [
    './UD_English/en-ud-dev.conllu',
    './UD_English/en-ud-test.conllu',
    './UD_English/en-ud-train.conllu'
]

CONNLU_NAMES = [
    'id',
    'form',
    'lemma',
    'upostag',
    'xpostag',
    'feats',
    'head',
    'deprel',
    'deps',
    'misc'
]

# Where to output words?
OUT_FILE = './parsed/ud_english_words.txt'

# Should we pad sentence boundaries? 0 if no padding, otherwise the number of
# dummy words in between sentences - this reduces word cooccurrences due to
# changed sentences
N_PADS = 5

import pandas as pd
from cStringIO import StringIO


def gen_padding(n):
    """
    Generate N fake words. All n words with underscores and postags will be
    returned space-separated as the first element of the list, except for the
    last nth word, which will have its postag as the second element

    e.g.

    ```
    In [22]: gen_padding(1)
    Out[22]: ['UD-DUMMY-0', 'X']

    In [23]: gen_padding(2)
    Out[23]: ['UD-DUMMY-0_X UD-DUMMY-1', 'X']
    ```
    """
    if n < 1:
        raise ValueError("Can't pad with n = ".format(n))

    all_dummies = ' '.join(
        ['UD-DUMMY-{}_X'.format(i) for i in xrange(n)]
    )
    last_pos = all_dummies.rfind('_')
    return [all_dummies[:last_pos], all_dummies[last_pos + 1:]]


if __name__ == '__main__':
    import argparse

    parser = argparse.ArgumentParser(
        formatter_class=argparse.ArgumentDefaultsHelpFormatter
    )

    args = parser.parse_args()

    all_ud = ''
    for fname in UD_FILES:
        with open(fname, 'r') as fin:
            all_ud += fin.read()

    ud = pd.read_table(StringIO(all_ud),
                       header=None,
                       names=CONNLU_NAMES,
                       na_values=['_'],
                       comment='#',
                       # Blank lines are sentence boundaries
                       # will replace NaNs later
                       skip_blank_lines=False)

    # We only care about lemmas and POS tags
    lemmas = ud[['lemma', 'upostag']]
    lemmas.is_copy = False

    # Just some weird hacking - I'm going to join columns, then write each
    # joined column separated by spaces, so NaN rows will look like 5 separate
    padding = gen_padding(N_PADS)

    lemmas.ix[lemmas.lemma.isnull(), 'lemma'] = padding[0]
    lemmas.ix[lemmas.upostag.isnull(), 'upostag'] = padding[1]

    words = lemmas.lemma.str.cat(lemmas.upostag, sep='_')

    # Output some statistics
    uniques = lemmas.ix[lemmas.upostag == 'VERB', 'lemma'].unique()
    print "Number of unique verb lemmas: {}".format(len(uniques))
    print uniques

    final_str = words.str.cat(sep=' ')

    with open(OUT_FILE, 'w') as fout:
        fout.write(final_str)
