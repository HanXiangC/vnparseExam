"""
Generating expanded verbnet matrices (ex) requires a mapping from
semantically-qualified PPs (e.g. PP.theme) to the actual prepositions (e.g.
about, after, for...)

Writes the extracted prepositional literals as a JSON object to a file.
"""

from bs4 import BeautifulSoup
import requests
import re
import vnerrors
import vnutil
from parse_verbnet import CSV_FORMAT_STR
from collections import defaultdict

VN_REFERENCE = "http://verbs.colorado.edu/verb-index/vn/reference.php"
EX_NS_COLS = 'parsed/ex-ns-columns.txt'
DOTQ_SOURCE = CSV_FORMAT_STR.format('gt-ns')

VISUAL_PREPS = "http://verbs.colorado.edu/verb-index/vn/preps.txt"
VISUAL_PREPS_LIST = [
    'dest_dir', 'dest_conf', 'dest', 'src', 'dir', 'path', 'loc', 'spatial'
]

ISA_RE = re.compile(b'isa\((\w+),(\w+)\)')
PP_DOTQ_RE = re.compile(b'PP\.([\w-]+)')
PREP_PP_RE = re.compile(b'([\w-]+)-PP')
PP_PREP_RE = re.compile(b'PP\.([\w-]+)')


def extract_pp_dotqs(frame):
    return re.findall(PP_DOTQ_RE, frame)


def extract_preps(text):
    prep_pps = re.findall(PREP_PP_RE, text)
    pp_preps = re.findall(PP_PREP_RE, text)
    preps = prep_pps + pp_preps
    # "NP-PP" matches the RE but doesn't counter.
    # Filter out what isn't necessary.

    def keep_prep(p):
        # Extend later
        return p not in ['NP', 'PP']

    return filter(keep_prep, preps)


# TODO: pp.initial_loc should be pp.initial_location
def extract_from_reference(url):
    r = requests.get(url)
    r.raise_for_status()
    soup = BeautifulSoup(r.content, 'lxml')
    # Following parents: text -> td -> tr -> table (what we're looking for)
    frame_types_table = soup.find(text='Frame Types').parent.parent.parent

    assert frame_types_table.name == 'table'
    dotqs = vnutil.dot_qualifiers(DOTQ_SOURCE)

    dotqs_to_preps = {}
    for dotq in dotqs:
        # Skip initial_loc
        if dotq == 'PP.initial_loc':
            continue
        # Shave off PP
        dotqs_to_preps[dotq.split('PP.')[1]] = set()
    # Need to recursively expand this.

    for frame_li in frame_types_table.find('ul'):
        if frame_li.name is None:
            continue
        # Each LI has the title text
        # <li>NP V NP <b>(n frames)</b> ...
        frame_incorrect = str(frame_li).split('<b>')[0].strip()
        # Shave off beginning <li>, strip whitespace, correct frame
        frame_correct = vnerrors.correct_frame(
            frame_incorrect.split('<li>')[1].strip()
        )
        #  print frame_correct
        pp_dotqs = extract_pp_dotqs(frame_correct)
        if pp_dotqs:
            # TODO: Put initial_loc frame into vnerrors??? YES
            if len(pp_dotqs) > 1:
                # Skip >1 dotq qualifier frames for now. It's not clear what
                # they mean!
                continue
            if pp_dotqs[0] == 'initial_loc':
                pp_dotqs[0] = 'initial_location'

            # Now find PPs mentioned in the nested UL
            preps = extract_preps(str(frame_li.find('ul')))
            literal_preps = filter(
                # Assume preps starting with capitals aren't literals
                lambda prep: not prep[0].isupper(),
                preps
            )
            dotqs_to_preps[pp_dotqs[0]].update(literal_preps)

    return dotqs_to_preps


def extract_from_columns(EX_NS_COLS):
    """
    NOTE: This takes from the previous ex_ns_cols. So, you may not want to run
    this unless you're looking for references like this.
    """
    with open(EX_NS_COLS, 'r') as fin:
        frames = fin.read().split(',')
    frames_list = [f.split() for f in frames]

    dotqs_to_preps = defaultdict(set)

    for frame in frames_list:
        for t1, t2 in zip(frame, frame[1:]):
            # Iterate two at a time. When you find a literal (islower)
            # and the second thing is an NP dotq then add to dictionary
            if (t1.islower() and '+' not in t1) and \
                    t2.startswith('NP.'):
                dotqs_to_preps[t2.split('NP.')[1]].add(t1)
    return dotqs_to_preps


def extract_from_visualpreps(url):
    """
    Plaintext file located at
    https://verbs.colorado.edu/verb-index/vn/preps.txt

    Intuition: begin building up strcture starting from smallest, then building
    up towards higher prepositions, following this:

    % Visual Preposition Class Hierarchy
    % ----------------------------------
    %   spatial
    %    |---> loc
    %    |---> path
    %           |---> dir
    %           |---> src
    %           |---> dest
    %                  |---> dest_conf
    %                  |---> dest_dir
    """
    r = requests.get(url)
    r.raise_for_status()
    lines = r.content.split('\n')
    vpreps_dict = {v: set() for v in VISUAL_PREPS_LIST}
    # We only care about lines that start with isa
    for line in lines:
        line = line.strip()  # Strip whitespace padding
        if line.startswith('isa'):
            # !!! Match from BEGINNING of line
            linematch = re.match(ISA_RE, line)
            literal, vprep_cat = linematch.group(1), linematch.group(2)
            # dissociate dynamic spatial ISAs
            if literal not in VISUAL_PREPS_LIST:
                vpreps_dict[vprep_cat].add(literal)
    # Now combine classes according to class hierarchy
    vpreps_dict['dest'].update(vpreps_dict['dest_dir'])
    vpreps_dict['dest'].update(vpreps_dict['dest_conf'])

    vpreps_dict['path'].update(vpreps_dict['dir'])
    vpreps_dict['path'].update(vpreps_dict['src'])
    vpreps_dict['path'].update(vpreps_dict['dest'])

    vpreps_dict['spatial'].update(vpreps_dict['loc'])
    vpreps_dict['spatial'].update(vpreps_dict['path'])

    return vpreps_dict


def merge_setdicts(*dicts):
    """
    Merge dicts into one dict. Assume these dicts have any typed keys, but SET
    values, because this method calls set.update()
    """
    dict_new = defaultdict(set)
    for d in dicts:
        for k, vset in d.iteritems():
            dict_new[k].update(vset)
    return dict_new


def jsonify_setdict(d):
    """
    Copy the dict, making it json-friendly by converting sets to lists
    """
    new_dict = {}
    for key in d:
        assert isinstance(d[key], set)
        new_dict[key] = list(d[key])
    return new_dict


if __name__ == '__main__':
    from argparse import ArgumentParser, ArgumentDefaultsHelpFormatter
    import json
    import os
    import sys
    parser = ArgumentParser(
        description=("Merge PP literals from various sources and "
                     "save to .json file"),
        formatter_class=ArgumentDefaultsHelpFormatter
    )
    parser.add_argument('-o', '--out', nargs=1, type=str,
                        default='./parsed/prep_literals.json',
                        help="Save literals to the given file")
    parser.add_argument('--from_columns', action='store_true',
                        help="Get literals from ex-ns-columns.txt")
    parser.add_argument('-O', '--overwrite', action='store_true',
                        help="Overwrite file without prompt")

    args = parser.parse_args()

    ref_preps = extract_from_reference(VN_REFERENCE)
    visual_preps = extract_from_visualpreps(VISUAL_PREPS)

    # Now merge
    all_preps = merge_setdicts(ref_preps, visual_preps)

    if args.from_columns:
        all_preps = merge_setdicts(
            all_preps, extract_from_columns(EX_NS_COLS)
        )

    # Write to json
    if os.path.isfile(args.out) and not args.overwrite:
        x = raw_input(
            "{} already exists. Overwrite? [y/N] ".format(args.out)
        ).lower()
        if x != 'y':
            print "Quitting..."
            sys.exit(0)

    to_json = jsonify_setdict(all_preps)
    with open(args.out, 'w') as fout:
        json.dump(to_json, fout)
