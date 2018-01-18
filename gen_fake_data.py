"""
This script will generate fake binary matrices data.

Currently, only traditional, "one-view" binary matrices are supported
(for clustering with the IRM).
"""

import numpy as np
import random
import seaborn as sns


def random_partition(n, k):
    """
    Randomly partition n (int) into k groups.
    Returns a list with length == k. Each element
    is a list containing the columns that have been randomly assigned.
    """
    # Get a list of indices to partition. To split into 3 partitions we want
    # 2 dividing indices (which will split into 3 groups).
    indices = [0]
    cols = range(n)
    random.shuffle(cols)
    indices.extend(sorted(random.sample(xrange(n), k - 1)))
    # We're going to grab slices based on each index range. So the last
    # index will be n.
    indices.append(n)
    return [cols[i:j] for (i, j) in zip(indices, indices[1:])]


def test_plot(arr, save_fname=None, plot=False):
    """
    Test plot using SNS clustermap. Clustermap uses hierarchical clustering
    on the rows and columns to reorder the graph. This makes low noise data
    look very nice, and also shows how well hierarchical clustering
    recovers data as noise increases.
    """
    cluster_plot = sns.clustermap(
        arr, vmin=0.0, vmax=1.0,
    )
    # Hide clustermap color key
    cluster_plot.cax.set_visible(False)
    if plot:
        sns.plt.show()
    if save_fname is not None:
        cluster_plot.savefig(save_fname)


def _epsilon(x):
    """Custom argparse "type" for epsilon."""
    x = float(x)
    if not (0.0 <= x <= 0.5):
        raise argparse.ArgumentTypeError(
            "{} not in range [0.0, 0.5]".format(x)
        )
    return x


def my_savetxt(fname, arr):
    """
    Savetxt with script settings.
    """
    np.savetxt(
        fname, arr, delimiter=',', fmt='%d'
    )


if __name__ == '__main__':
    import argparse
    import os
    import sys
    # We need to increase the recursion limit to plot larger dendrograms
    sys.setrecursionlimit(10000)
    parser = argparse.ArgumentParser(
        formatter_class=argparse.ArgumentDefaultsHelpFormatter
    )
    parser.add_argument('clusters', nargs='?', type=int, default=2,
                        help=("Comma-separated list of integers, each "
                              "representing the number of clusters in a view. "
                              "Right now, partitioning is done uniformly "
                              "randomly."))
    parser.add_argument(
        '-r', '--rows', type=int, default=6334,
        help="Number of rows in the dataset. NOTE: implicit uint16 limit"
    )
    parser.add_argument(
        '-c', '--cols', type=int, default=285,
        help="Number of cols in the dataset. NOTE: implicit uint16 limit"
    )
    parser.add_argument('-R', '--rng_seed', type=int, default=None,
                        help="RNG random seed (defaults to system time)")
    parser.add_argument('-e', '--epsilon', type=_epsilon, default=0.0,
                        help=("Epsilon noise parameter in [0.0, 0.5]. "
                              "For each cell in the finished array, "
                              "this is the likelihood that the cell will "
                              "switch."))
    parser.add_argument(
        '-o', '--out', type=str,
        default='./fake/{rows}x{cols}-e{epsilon}-{clusters}clus.csv',
        help=("Format string for output data. Variable "
              "names in args are used to format the string, "
              "so feel free to use those.")
    )
    parser.add_argument('-P', '--plot', action='store_true',
                        help="Plot seaborn clustermap to visualize data")
    parser.add_argument('-S', '--save_plot', action='store_true',
                        help="Save seaborn clustermap image in fake/img/")
    parser.add_argument('-O', '--overwrite', action='store_true',
                        help=("If file already exists, overwrite without "
                              "prompt"))
    parser.add_argument('-H', '--header', default=[],
                        help=("Header (not yet implemented)"))

    args = parser.parse_args()

    if args.header:
        raise NotImplementedError("No header support")

    # Should have one extra for rows and headers!
    dim = (args.rows + 1, args.cols + 1)

    # Not bool, since there will be numeric names
    arr = np.zeros(dim, dtype=np.uint16)

    fname = args.out.format(**vars(args))

    # Process view_clusters by splitting on commas, stripping whitespace, turn
    # converting to int

    # Determine random partitioning, set seed first
    random.seed(args.rng_seed)
    col_partitions = random_partition(args.cols, args.clusters)
    row_partitions = random_partition(args.rows, args.clusters)
    for rowp, colp in zip(row_partitions, col_partitions):
        # http://stackoverflow.com/questions/22927181/
        # selecting-specific-rows-and-columns-from-numpy-array
        arr[1:, 1:][np.array(rowp)[:, None], np.array(colp)] = 1

    # Create noise array
    noise = np.random.binomial(1, args.epsilon, size=arr[1:, 1:].shape)
    # orig noise | out
    # 0    0     | 0
    # 0    1     | 1   (Toggle)
    # 1    0     | 1
    # 1    1     | 0   (Toggle)
    # This is xor!
    arr[1:, 1:] = np.bitwise_xor(arr[1:, 1:], noise)

    # Now fill in rownames, colnames
    # We need rows and cols to start from 0 to match up with sns clsutermap
    arr[1:, 0] = np.arange(arr.shape[0] - 1)
    arr[0, 1:] = np.arange(arr.shape[1] - 1)
    # Because I'm not sure if this needs to exist, just fill it in with 0
    # XXX: Might be a possible source of duplicate rowname bug in the future
    arr[0, 0] = 0

    if args.plot or args.save_plot:
        test_plot(
            arr[1:, 1:],
            # Swap fake/ directory with fake/img/ directory, .csv with .png
            save_fname=('fake/img' + fname.split('.csv')[0][6:] + '.png'
                        if args.save_plot else None),
            plot=args.plot
        )

    if os.path.exists(fname):
        if not args.overwrite:
            x = raw_input(
                "File {} already exists, overwrite? [y/N] ".format(fname)
            ).lower()
            if x == 'y' or x == 'yes':
                my_savetxt(fname, arr)
        else:
            my_savetxt(fname, arr)
    else:
        my_savetxt(fname, arr)
