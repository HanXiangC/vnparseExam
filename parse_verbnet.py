"""
Toplevel script used to create vn matrices.
"""

import vnparser
import vnutil
from collections import defaultdict

# Verbnet location
VN_DIR = './new_vn/'
DATA_DIR = './parsed/'

# Frame format strings
FORMATS = [
    # Groundtruth
    'gt-ns',  # No semantics
    'gt-ss',  # Semantics
    'gt-tr',  # Theta roles
    # Collapsed syntax
    'cx-ns',
    'cx-ss',
    'cx-tr',
    # Collapsed syntax
    # Expanded syntax
    'ex-ns',
    'ex-ss',
    'ex-tr',
    # Special "expanded/collapsed" syntax
    'ex-cx',
    # Special "expanded/collapsed and theta roles" syntax
    'et-cx',
    # Adding selectional restrictions AND thematic roles
    # with both expanded/collapsed prepositions
    'cx-st',
    'ex-st'
]

# Templates for filenames
CSV_FORMAT_STR = DATA_DIR + 'vn-{}{}.csv'
CSV_SHORT_FORMAT_STR = DATA_DIR + 'vn-{}{}-short.csv'
COLUMNS_FORMAT_STR = DATA_DIR + '{}{}-columns.txt'

NONTOPICS_FNAME = DATA_DIR + 'nontopics{}.txt'
MEMBERS_FNAME = DATA_DIR + 'members{}.txt'
MEMBERS_SHORT_FNAME = DATA_DIR + 'members-short{}.txt'
GT_TOP_FNAME = DATA_DIR + 'gt-top{}.txt'
GT_FNAME = DATA_DIR + 'gt{}.txt'
GTSUB_FNAME = DATA_DIR + 'gtsub{}.txt'
GT_SHORT_FNAME = DATA_DIR + 'gt-short{}.txt'
# Cluster assignment for GT_SHORT by clustering on toplevel matches
GT_SHORT_TOP_FNAME = DATA_DIR + 'gt-top-short{}.txt'

# Json-encoded verbnet -> wordnet map
VN_WN_MAP_FNAME = DATA_DIR + 'vnwn{}.json'


class ClusterCounter(object):
    """Neat wrapper around a autoincrementing defaultdict."""
    def __init__(self, cnum=0):
        self._cnum = cnum

        def new_cluster():
            self._cnum += 1
            return self._cnum

        self.autocounter = defaultdict(new_cluster)

    def get(self, val):
        return self.autocounter[val]

    @property
    def numclus(self):
        """Since cnum starts at 0."""
        return self._cnum + 1


def main(formats, srsref=None, short=True, verbs_only=False):
    """Do everything."""
    # Get the minimal verbnet representation
    vn = vnparser.parse_vn(VN_DIR, srsref)
    vncsv = None

    vo_str = '-vo' if verbs_only else ''

    for fmt in formats:
        csv_fname = CSV_FORMAT_STR.format(fmt, vo_str)
        columns_fname = COLUMNS_FORMAT_STR.format(fmt, vo_str)

        try:
            vncsv = vn.to_csv(fmt=fmt, verbs_only=verbs_only)
        except NotImplementedError:
            print("{} not implemented, skipping...".format(fmt))
            continue
        vnutil.save_csv(vncsv, csv_fname)
        if short:
            csv_short_fname = CSV_SHORT_FORMAT_STR.format(fmt, vo_str)
            shortened = vnutil.shorten_vn(vncsv)
            vnutil.save_csv(shortened, csv_short_fname)

        columns = vnutil.get_csv_columns(vncsv)
        vnutil.save_list(columns, columns_fname)

    # This is OUTSIDE the for loop - we only need one members file!
    if vncsv is None:
        # We never parsed any csv files. So just return return
        print "No csv files parsed, exiting without saving members or clusters"
        return

    # Save nontopics verbs
    nontopics = vn.get_nontopic_verbs()
    vnutil.save_list(nontopics, NONTOPICS_FNAME.format(vo_str))

    # Save members
    members = vnutil.get_csv_members(vncsv)
    vnutil.save_list(members, MEMBERS_FNAME.format(vo_str))

    # NEW: Save vn mapping
    vnwn = vn.verbnet_wordnet_map()
    vnutil.save_json(vnwn, VN_WN_MAP_FNAME.format(vo_str))

    # Save shortened members
    if short:
        members_short = vnutil.get_csv_members(shortened)
        vnutil.save_list(members_short, MEMBERS_SHORT_FNAME.format(vo_str))

    # Verbnet v3.2 assertion

    # Other useful data sources - verbnet cluster assignments
    gt = []
    gtsub = []
    gt_top = []
    gt_counter = ClusterCounter()
    gtsub_counter = ClusterCounter()
    gt_top_counter = ClusterCounter()
    for member in members:
        vnclass_full = vnutil.get_vnclass(member)
        vnclass_top = vnutil.get_toplevel(vnclass_full)
        vnclass_int = vnutil.get_int_str(vnclass_full)

        gt.append(gt_counter.get(vnclass_top))
        gtsub.append(gtsub_counter.get(vnclass_full))
        gt_top.append(gt_top_counter.get(vnclass_int))

    vnutil.save_list(map(str, gt), GT_FNAME.format(vo_str))
    vnutil.save_list(map(str, gtsub), GTSUB_FNAME.format(vo_str))
    vnutil.save_list(map(str, gt_top), GT_TOP_FNAME.format(vo_str))

    if short:
        # Shortened cluster assignments. We don't use gtsub_short because
        # the members are themselves gtsubs!
        gt_short = []
        gt_counter_short = ClusterCounter()
        for member_short in members_short:
            vnclass_top_short = vnutil.get_toplevel(member_short)

            gt_short.append(gt_counter_short.get(vnclass_top_short))

        vnutil.save_list(map(str, gt_short), GT_SHORT_FNAME.format(vo_str))

        # Save "top" only if we save "short"
        gt_short_top = []
        gt_counter_short_top = ClusterCounter()
        for member_short in members_short:
            # In this case, our "top" encoding is all unique
            # n(.n)* (we don't truncate the floats with get_n)
            top_n = vnutil.get_int(member_short)

            gt_short_top.append(gt_counter_short_top.get(top_n))

        vnutil.save_list(map(str, gt_short_top),
                         GT_SHORT_TOP_FNAME.format(vo_str))


if __name__ == '__main__':
    from argparse import ArgumentParser, ArgumentDefaultsHelpFormatter
    import json
    import sys
    parser = ArgumentParser(
        description="Parse by invoking vnparser.parse_vn, save to csv",
        formatter_class=ArgumentDefaultsHelpFormatter
    )
    parser.add_argument('formats', nargs='*', type=str)
    parser.add_argument('-A', '--all', action='store_true',
                        help="Create all csv formats")
    parser.add_argument('-O', '--overwrite', action='store_true',
                        help="Overwrite (all!) existing files")
    parser.add_argument('--no_short', action='store_true',
                        help="Don't create shortened CSVs (we do by default)")
    parser.add_argument('--verbs_only', action='store_true',
                        help="Create matrices with verbs only (no vnclass)")
    parser.add_argument('-d', '--dot_qualifiers', action='store_true',
                        help="Totally different: print dot qualifiers")
    parser.add_argument('-s', '--selrestr_reference', type=str,
                        default='./parsed/prep_literals.json',
                        help="JSON-encoded selrestrs->literals reference")

    args = parser.parse_args()

    if args.formats and args.all:
        parser.error("can't specify formats and --all")

    if not args.formats and not args.all:
        parser.error("must specify formats or --all")

    try:
        with open(args.selrestr_reference, 'r') as fin:
            srsref = json.load(fin)
    except IOError:
        parser.error(
            "couldn't open {}.\n\tDid you run get_prep_literals.py?".format(
                args.selrestr_reference
            )
        )
        sys.exit(1)

    # !!! Convert srsref list vals into sets (json doesn't allow lists)
    for vprep in srsref:
        srsref[vprep] = set(srsref[vprep])

    if args.dot_qualifiers:
        dotqs = vnutil.dot_qualifiers(CSV_FORMAT_STR.format('gt-ns'))
        for dotq in dotqs:
            print dotq
    elif args.all:
        main(FORMATS, srsref, not args.no_short, args.verbs_only)
    else:
        main(args.formats, srsref, not args.no_short, args.verbs_only)
