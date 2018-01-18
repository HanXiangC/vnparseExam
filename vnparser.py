"""
Parse verbnet version 3.2
NLTK doesn't have the latest version of verbnet available
 self.
Jesse Mu
"""

from bs4 import BeautifulSoup
import glob
from collections import defaultdict
import vnerrors
from vnutil import flatten
from vncomponents import (
    ThemroleSelrestr, Themrole, Verb, Pos, Token, Frame, TokenSelrestr
)
from verbnet import VerbNet
import itertools


def extend_themroles(themroles_soup, roles):
    """
    Get the toplevel thematic roles associated with a vnclass.
    """
    for trole in filter_empty(themroles_soup.children):
        roletype = trole['type']
        all_selrestrs = trole.find_all('SELRESTRS')
        all_selrestr_tp = ()
        for selrestrs in all_selrestrs:
            logical_or = False
            selrestr_tp = ()
            if selrestrs and selrestrs.text:
                if selrestrs.has_attr('logic'):
                    # XXX: But it could be 'and'?
                    # XXX: Where did the logical_ands go??
                    assert selrestrs['logic'] == 'or'
                    logical_or = True
                selrestr_list = selrestrs.find_all('SELRESTR')
                for selrestr in selrestr_list:
                    selrestr_tp += (selrestr['Value'] + selrestr['type'], )
            all_selrestr_tp += (ThemroleSelrestr(selrestr_tp,
                                                 logical_or=logical_or), )
        roles += (Themrole(roletype, all_selrestr_tp), )
    # Added 20160106: Get rid of duplicates when roles are updated
    return Themrole.merge_themrole_list(roles)


def members_and_frames(vnclass, frames=None, roles=()):
    """
    Return a tuple (members, frames) where members is the list of verbs
    (for now, basic infinitive form) and frames is the list of syntactic
    frames in the class applicable to each member (again, for now, the basic
    descriptive term).

    vnclass is a BeautifulSoup object. It could be a top-level class (xml file)
    or a subclass, they're treated the same. Regardless, it must be *exactly*
    the xml node vnclass or vnsubclass, as the nonrecursive search for members
    and frames depends on knowing the depth of the member and frame nodes.
    """
    # Nonrecursive search is essential so we don't grab members of the
    # subclasses if they exist
    members = []
    class_id = vnclass['ID']
    for mem in vnclass.find('MEMBERS', recursive=False).find_all('MEMBER'):
        members.append(
            Verb(mem['name'], class_id, mem['wn'].split(),
                 mem['grouping'] if 'grouping' in mem else None)
        )

    if frames is None:  # Avoid mutable default argument
        frames = []
    else:
        frames = frames[:]  # Copy frames to avoid mutation

    themroles_soup = vnclass.find('THEMROLES')
    # TODO: Validate roles validity - is it being passed through
    # the recursion correctly?
    roles = extend_themroles(themroles_soup, roles)

    # Since frames is a list, this doesn't check for duplicates. That's okay,
    # as duplicates are removed in building the frames dict
    for frame in vnclass.find('FRAMES', recursive=False).find_all('FRAME'):
        desc = frame.find('DESCRIPTION')
        primary = desc['primary']
        # TODO: Start here. A frame now needs to contain syntactic information
        # as well TODO: assert that a PREP either has VALUE = space-separated
        # list of preps or NONEMPTY selrestrs. Then collect the selrestrs
        # to figure out the stuff that we don't know that we need to use.
        # (e.g. +loc). Need to figure out what that means, +loc?
        # What to do is, sometimes PP.location may have specific
        # preps. So begin constructing a class that way.
        # also parse the other lists of things.
        frame = construct_frame(frame, primary, roles, class_id)
        frames.append(frame)

    # Sanity checks
    if not (members or frames):
        print "Warning: Class {} has no members and no frames".format(
            vnclass['ID']
        )
    elif not members:
        print "Warning: Class {} has frames {} but no members".format(
            vnclass['ID'], frames
        )
    elif not frames:
        print "Warning: Class {} has members {} but no frames".format(
            vnclass['ID'], members
        )

    # Construct the global mf list and begin extending with recursive calls
    all_mf = [(members, frames)]

    # Get subclasses
    vnsubclasses = vnclass.find('SUBCLASSES', recursive=False)
    if vnsubclasses:
        subclass_list = vnsubclasses.find_all('VNSUBCLASS', recursive=False)
        # Subclass list could still be empty, as there are empty
        if subclass_list:
            for subc in subclass_list:
                all_mf.extend(
                    members_and_frames(subc, frames=frames, roles=roles)
                )

    return all_mf


def display_stats(all_mf):
    """Display useful info about the parsed verbnet corpus."""
    members = flatten(t[0] for t in all_mf)
    members_uniq = set(members)
    print "# members: {}".format(len(members))
    print "unique: {}".format(len(members_uniq))  # Check for duplicates
    frames = flatten(t[1] for t in all_mf)
    frames_uniq = set(frames)
    print "# frames: {}".format(len(frames))
    print "unique: {}".format(len(frames_uniq))


def construct_frames_dict(all_mf):
    """
    Given the list of nested members and frames tuples, construct a dictionary
    with member keys and list of frames values for constructing a CSV.
    """
    frames_dict = defaultdict(set)
    for members, frames in all_mf:
        for mem in members:
            for frame in frames:
                # With duplicate frames this works fine since set removes dups
                frames_dict[mem].add(frame)
    return frames_dict


def filter_empty(children):
    """
    Helper function to get rid of weird empty line BeautifulSoup children.
    """
    return filter(lambda n: n.name is not None, children)


def parse_token(node):
    """
    Given the BeautifulSoup objet of a verbnet token, return a corresponding
    Token object.
    """
    if node.name == 'LEX':
        assert not node.has_attr('selrestrs') and \
            not node.has_attr('synrestrs')
        return Token(Pos.LEX, node['value'])
    elif node.name == 'NP':
        synrestr_tp = ()
        synrestrs = node.find('SYNRESTRS')
        if synrestrs and synrestrs.text:
            for sr in filter_empty(synrestrs.children):
                # Tuple addition is slow, but these tokens
                # should be immutable!
                synrestr_tp += (sr['Value'] + sr['type'], )

        selrestr_tp = ()
        selrestrs = node.find('SELRESTRS')
        if selrestrs and selrestrs.text:
            for sr in filter_empty(selrestrs.children):
                selrestr_tp += (sr['Value'] + sr['type'], )

        logical_or = logical_and = False
        if selrestrs and selrestrs.has_attr('logic'):
            if selrestrs['logic'] == 'or':
                logical_or = True
            elif selrestrs['logic'] == 'and':
                logical_and = True
            else:
                raise Exception("Found NP logic that's not or or and")

        # Let assert_valid in token validate xor of selrestr and synrestrs.
        selrestrs_class = TokenSelrestr(selrestr_tp, logical_or, logical_and)
        return Token(Pos.NP, node['value'], selrestrs=selrestrs_class,
                     synrestrs=synrestr_tp)
    elif node.name == 'VERB':
        return Token(Pos.VERB)
    elif node.name == 'PREP':
        # Construct selectional restrictions
        selrestr_tp = ()
        selrestrs = node.find('SELRESTRS')
        for sr in filter_empty(selrestrs.children):
            selrestr_tp += (sr['Value'] + sr['type'], )

        # Get value if exists
        value = None
        if node.has_attr('value'):
            # TODO: Do I need to split on whitespace?
            value = node['value']
            assert not selrestr_tp
        else:
            assert selrestr_tp
        # Assert no synrestrs
        assert not node.find('SYNRESTRS')
        # Construct class from the selrestrs_tp
        # Check logical or and logical and
        logical_or = logical_and = False
        if selrestrs.has_attr('logic'):
            if selrestrs['logic'] == 'or':
                logical_or = True
            elif selrestrs['logic'] == 'and':
                logical_and = True
            else:
                import ipdb; ipdb.set_trace()
                raise Exception("Found prep logic that's not or or and")

        selrestrs_class = TokenSelrestr(selrestr_tp, logical_or, logical_and)

        return Token(Pos.PREP, value, selrestrs=selrestrs_class)
    elif node.name == 'ADJ':
        return Token(Pos.ADJ)  # Doesn't seem like there's anything in here
    elif node.name == 'ADV':
        # NOTE: Assmption here is that in the frame, ADV always begins with
        # capitals ADV
        # There are various kinds of adverbs, some that are codified only
        # in the primary description. However, to maintain primary tokens and
        # syntax tokens independence, I don't care about those.
        # Find correct representation of this adverb located in the primary
        # description, since it can be ADV-Middle, ADVP, etc.
        # value = None
        # for t in primary_tokens:
            # if t.startswith("ADV"):
                # assert not value, str(primary_tokens)
                # value = t
        # assert value, str(primary_tokens) + str(node)
        return Token(Pos.ADV)
    else:
        raise ValueError("Unknown xml name {}".format(node.name))


def construct_frame(frame, primary, roles, class_id):
    """
    Construct the Frame representation of the BeautifulSoup object.
    Primary is the string representation stored in the primary
    attribute of the frame XML node.
    """
    # Important! Error correction
    primary = vnerrors.correct_frame(primary, class_id)
    # Implicitly, splitting on whitespace here does some error correction on
    # its own - removes stray colon in sound_emission-43.2, extra spaces
    # in random frames, etc
    primary_tokens = tuple(primary.split())
    syntax_soup = frame.find('SYNTAX')
    children = list(syntax_soup.children)
    # Remove empty elements
    real_children = filter_empty(children)
    tokenized = tuple(itertools.imap(parse_token, real_children))
    # TODO: Start here. A frame now needs to contain syntactic information
    # as well
    return Frame(primary_tokens, tokenized, roles, class_id)


def parse_vn(vn_dir, srsref=None):
    """
    Return a Verbnet wrapper instance of the given directory (see class def!)

    Ensure srsref's values are of type SET.
    """
    all_mf = []
    for fname in glob.glob(vn_dir + '*.xml'):
        with open(fname, 'r') as fin:
            fsoup = BeautifulSoup(fin.read(), 'xml')  # Specify xml not html
            topclass = fsoup.find('VNCLASS')
            all_mf.extend(members_and_frames(topclass))

    display_stats(all_mf)
    vn = construct_frames_dict(all_mf)
    return VerbNet(vn, srsref)
