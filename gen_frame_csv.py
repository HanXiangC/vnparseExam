"""
For obtaining correspondence between finer- and coarser-grained frames, this
script creates a CSV that maps all finest-grained frames (ex-st) to every one
of their coarser-grained variants.
"""

import vnutil
import vnparser
from parse_verbnet import VN_DIR, DATA_DIR
import json

import pandas as pd

from collections import defaultdict

# The formats actually to be used in publication, not including
# ex-st (the most fine-grained frame)
FINEST = 'ex-st'
ALL_PUB = [
    'gt-ns',
    'cx-ns',
    'ex-cx',
    'cx-tr',
    'et-cx',
    'cx-ss',
    'ex-ss',
    'cx-st',
]

FOUT = DATA_DIR + 'frames.csv'


def other_variants(frame, srsref=None):
    others = []
    for other_fmt in ALL_PUB:
        sub_others = frame.format(fmt=other_fmt, srsref=srsref)

        others.append(sorted(sub_others))

    return others

if __name__ == '__main__':
    from argparse import ArgumentParser, ArgumentDefaultsHelpFormatter
    import sys

    parser = ArgumentParser(formatter_class=ArgumentDefaultsHelpFormatter)

    parser.add_argument('-s', '--selrestr_reference', type=str,
                        default='./parsed/prep_literals.json',
                        help="JSON-encoded selrestrs->literals reference")

    args = parser.parse_args()

    srsref = vnutil.load_srsref(args.selrestr_reference)

    vn = vnparser.parse_vn(VN_DIR, srsref)

    frames = defaultdict(list)
    for frameset in vn._vn.values():
        for frame in frameset:
            # Parse into finest-grained format
            # Sort them to ensure variants are in the right direction
            frame_strs = sorted(frame.format(fmt=FINEST, srsref=srsref))

            # Get other variants
            others = other_variants(frame, srsref)

            # Assign other variants to every frame in frame_strs
            for i, fs in enumerate(frame_strs):

                others_sub = []
                for oth in others:
                    if len(oth) > 1:
                        assert len(oth) == len(frame_strs)
                        try:
                            others_sub.append(oth[i])
                        except Exception as e:
                            print oth
                            print frame_strs
                            raise e
                    else:
                        others_sub.append(oth[0])

                if fs in frames:
                    if frames[fs] != others_sub:
                        # Then it's probably the first one with a difference
                        # Then assign frames[fs] whichever is SHORTER (so
                        # getting rid of NP.themes)
                        if len(others_sub[0]) < len(frames[fs][0]):
                            frames[fs] = others_sub
                else:
                    frames[fs] = others_sub

    df = pd.DataFrame(data=frames, index=ALL_PUB).T
    # Should you replace spaces with dots here?

    df.to_csv(FOUT)
