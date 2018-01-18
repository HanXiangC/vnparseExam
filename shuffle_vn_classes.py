import vnutil
from collections import Counter
from random import shuffle
import pandas as pd


def get_classes_count(df):
    classes_counts = long.index.map(lambda x: x.split('#')[1])

    return Counter(classes_counts)


def make_shuffled_csv(long, short, sizes):
    shuffled_tuples = []
    for csv_tuple, sampled_size in zip(short.iterrows(), sizes):
        vnclass, data = csv_tuple
        for token_i in xrange(sampled_size):
            vnclass_i = '{}#{}'.format(vnclass, token_i)
            shuffled_tuples.append((vnclass_i, data))

    assert len(shuffled_tuples) == long.shape[0]

    return pd.DataFrame.from_items(shuffled_tuples,
                                   columns=short.columns,
                                   orient='index')


if __name__ == '__main__':
    from argparse import ArgumentParser

    parser = ArgumentParser()
    parser.add_argument('verbnet_format', nargs='?', default='et-cx')
    parser.add_argument('-n', type=int, default=10)

    args = parser.parse_args()

    print "Shuffling CSV {} {} times".format(
        args.verbnet_format,
        args.n
    )

    # Must be something like et-cx, 5char
    assert len(args.verbnet_format) == 5, 'Invalid verbnet format'

    short_csv = './parsed/vn-{}-short.csv'.format(args.verbnet_format)
    long_csv = './parsed/vn-{}.csv'.format(args.verbnet_format)

    short = vnutil.load_df(short_csv)
    long = vnutil.load_df(long_csv)

    assert all(short.columns == long.columns)

    classes_counter = get_classes_count(long)
    classes_n = sorted(classes_counter.values(), reverse=True)

    assert len(classes_n) == short.shape[0]

    for i in xrange(args.n):
        print "Shuffling #{}".format(i)
        shuffle(classes_n)

        # Coerce to int for faster writing
        shuffled_csv = make_shuffled_csv(long, short, classes_n) * 1
        to_write_csv = './parsed/shuffled/vn-{}-shuffled-{}.csv'.format(
            args.verbnet_format,
            i
        )

        shuffled_csv.to_csv(to_write_csv)
