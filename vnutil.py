"""
Utility functions for loading and saving files, among others.
"""

import numpy as np
import pandas as pd
import csv
import json
from collections import defaultdict


def load_df(fname):
    """
    Load the matrix associated with the given .csv file into a dataframe.

    We don't use pandas.read_csv because our csv doesn't have a well-formed
    "index" column (it's labeled under the column "members" like the rest of
    the frames).
    """
    with open(fname, 'r') as fin:
        reader = csv.reader(fin)
        binmat = list(reader)
    header = binmat[0][1:]
    members, cols = zip(*((r[0], r[1:]) for r in binmat[1:]))
    cols = np.array(cols)
    df = pd.DataFrame(data=cols, index=members, columns=header, dtype=bool)
    return df


def save_csv(matrix, fname, quiet=False):
    """
    Write a matrix to the given filename.
    Make sure the matrix has a header with first column "member"!
    """
    with open(fname, 'w') as fout:
        writer = csv.writer(fout)
        writer.writerows(matrix)
    if not quiet:
        print "CSV saved in {}".format(fname)


def save_list(lst, fname, quiet=False):
    """
    Write a list to the given filename.
    """
    with open(fname, 'w') as fout:
        fout.write(','.join(lst))
    if not quiet:
        print "List saved in {}".format(fname)


def load_list(fname, sep=',', quiet=True):
    """
    Load the given `sep`-delimited text file into a list
    """
    with open(fname, 'r') as fin:
        a = fin.read().strip().split(sep)
    if not quiet:
        print "Read {} elements from {}".format(len(a), fname)
    return a


def save_json(obj, fname, quiet=False):
    """
    Dump a (hopefully valid) JSON object to the given filename.
    """
    with open(fname, 'w') as fout:
        json.dump(obj, fout)
    if not quiet:
        print "JSON dumped in {}".format(fname)


def load_json(fname, quiet=True):
    """
    Dump a (hopefully valid) JSON object to the given filename.
    """
    with open(fname, 'r') as fin:
        j = json.load(fin)
    if not quiet:
        print "JSON dumped in {}".format(fname)
    return j


def flatten(lst):
    """
    Utility function used to flatten lists (or generators!) with nested tuples.
    """
    return [item for sublist in lst for item in sublist]


def unique_frames(vn_str):
    """
    Given a stringified dictionary, return the unique set of string frame
    elements in all dictionary values.

    This function works independently of any syntactic/semantic vn format.
    """
    all_frames = []
    for verb in vn_str:
        all_frames.extend(vn_str[verb])
    return set(all_frames)


def get_csv_members(vncsv):
    """
    Get the list of members from a given verbnet csv (produced with
    to_csv and a specified format).
    """
    return [row[0] for row in vncsv[1:]]  # Skip header row


def get_csv_columns(vncsv):
    """
    Get the list of columns from a given verbnet csv (produced with
    to_csv and a specified format).
    """
    return vncsv[0][1:]  # Skip "member" column


def dot_qualifiers(fname):
    """
    Print dot qualifiers for the given CSV columns. Useful for vn-ex, where I
    need a list of prepositions.

    Run this on groundtruth (vn-gt-ns.csv) for best results.
    """
    dot_qualified = set()
    df = load_df(fname)
    for cl in df.columns:
        for token in cl.split():
            if "PP." in token:
                dot_qualified.add(token)

    return list(dot_qualified)


def flatten_and_unique(nested_flist):
    """Flatten a nested list AND remove its duplicates."""
    unnested = [item for sublist in nested_flist for item in sublist]
    return list(set(unnested))


def pp_str_to_np_str(ppstr):
    """
    Convert a PP token to an NP token, *in string form*. Used for expanding
    matrices after extracting literals out of PPs.

    NOTE: This keeps the dotq. Might have to strip that using something else.
    """
    assert ppstr.startswith('PP')
    return 'N' + ppstr[1:]


def get_vnclass(member, raise_if_none=False):
    """
    Given the full member encoded as member#vnclass, return only the vnclass,
    or None if none is detected.
    """
    try:
        return member.split('#')[1]
    except IndexError:
        if raise_if_none:
            raise ValueError("No member found for {}".format(member))
        return None


def get_toplevel(vnclass):
    """
    Given a vnclass with possible subclasses, get the toplevel vnclass.

    Form is always classdesc-n.n.n...*-C-C-C...*, where -Cs are the
    subclasses. So split on dashes, then join the first two dashes.

    NOTE: Make sure to pass in a VNCLASS, not a member!
    """
    return ''.join(vnclass.split('-')[:2])


def get_float_str(vnclass):
    """
    Get the numeric code for the vnclass, represented as a STRING. Different
    from get_n, which returns a float.

    Why? Because some vnclasses have 2+ period qualifiers, e.g.
    10.4.3
    10.2.5

    get_n truncates 2+ dots to the single-decimal float (10.4, 10.2)
    """
    # Doesn't matter whether we're handed a toplevel or subclass or even
    # member, since from member#classdesc-n.n.n-c-c-c..., since splitting
    # on dashes will return [blah, n.n.n, blah*] and we get the 1st element
    return vnclass.split('-')[1]


def get_float(vnclass):
    """
    Return the numeric code for the vnclass as a FLOAT. NOTE: Truncates
    double-dotted codes (e.g. 10.4.3; see get_n_str)
    """
    # Same as before but split on .s and parse the float.
    long_str = vnclass.split('-')[1]
    return float('.'.join(long_str.split('.')[0:2]))


def get_float_ext(vnclass):
    """
    Return the numeric code for the vnclass as a FLOAT, but differentiates
    between double-dotted codes by adding an extra small amount.
    """
    raise NotImplementedError


def get_int(vnclass):
    """
    Return only the *integer* portion of the numeric code (so the
    top-top-toplevel classes)
    """
    return int(vnclass.split('-')[1].split('.')[0])


def get_int_str(vnclass):
    """
    Return only the *integer* portion of the numeric code as string.
    """
    return str(get_int(vnclass))


def hierarchy_tuple(vnclass, full_leaf_name=False):
    """
    Given a vnclass, return its "hierarchy tuple": i.e.
    (10, 10.1, 10.1.1, class-name, 1, 1-1, 1-3)
    If at any point the division of the given class doesn't exist,
    we put 0s instead. For example, the simple
    body_internal_motion-49 will have
    (49, 49.0, 49.0.0, body_internal_motion, 0, 0-0, 0-0-0)

    If full_leaf_name, then the leaf will not be 0-0-0, but rather the full
    vnclass name.
    """
    # Initialize list, convert to tuple later
    hier = []

    # Toplevel has format i.j.k. Determine what i, j, k are by parsing the
    # float
    components = get_float_str(vnclass).split('.')
    try:
        i = components[0]
    except IndexError:
        i = 0
    try:
        j = components[1]
    except IndexError:
        j = 0
    try:
        k = components[2]
    except IndexError:
        k = 0
    hier.append('{}'.format(i))
    hier.append('{}.{}'.format(i, j))
    hier.append('{}.{}.{}'.format(i, j, k))

    # Append vn name
    # class-m.m.m-n-n-n; so split on -s and get 0th
    hier.append(vnclass.split('-')[0])

    # Append vnclasses in a similar way. Set l, m, n
    # Probably more efficient to use list
    subclasses = vnclass.split('-')[2:]
    try:
        l = subclasses[0]
    except IndexError:
        l = 0
    try:
        m = subclasses[1]
    except IndexError:
        m = 0
    try:
        n = subclasses[2]
    except IndexError:
        n = 0
    hier.append('{}'.format(l))
    hier.append('{}-{}'.format(l, m))
    if full_leaf_name:
        hier.append(vnclass)
    else:
        hier.append('{}-{}-{}'.format(l, m, n))
    return tuple(hier)


def shorten_vn(vncsv):
    """
    "Shorten" the given VerbNet csv by collapsing VerbNet members down to
    classes.
    """
    shortened = [vncsv[0]]  # Start with header row
    seen_vnclasses = set()
    for row in vncsv[1:]:
        vnc = get_vnclass(row[0])
        if vnc not in seen_vnclasses:
            seen_vnclasses.add(vnc)
            shortened.append([vnc] + row[1:])
    return shortened


def load_srsref(fname):
    """
    Load srsref at the given filename
    """
    try:
        with open(fname, 'r') as fin:
            srsref = json.load(fin)
    except IOError:
        raise IOError(
            "Couldn't open {}.\n\tRun get_prep_literals.py".format(fname)
        )

    # !!! Convert srsref list vals into sets (json doesn't allow lists)
    for vprep in srsref:
        srsref[vprep] = set(srsref[vprep])

    return srsref


def get_classes_verbs_dict(members_file):
    """
    Given the list of members
    Return a dictionary containing vnclasses mapped to their verbs
    """
    if 'members' not in members_file:
        print "Warning: members not detected in members file"
    members = load_list(members_file)
    cvdict = defaultdict(list)
    for m in members:
        verb, vnclass = m.split('#')
        cvdict[vnclass].append(verb)
    return cvdict


def dot(frame):
    """
    Given a frame, dot it to make it a valid R name
    (I shouldn't have made this mistake in the first place)
    """
    raise NotImplementedError
