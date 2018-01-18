"""
Toplevel verbnet class.
"""

from vnutil import flatten_and_unique, unique_frames
from collections import defaultdict


class VerbNet(object):
    """
    Verbnet object representation.
    """
    def __init__(self, vn, srsref=None):
        """
        Initialize the verbnet object. Vn is the dictionary with member keys
        and frames values as returned by parse_vn.
    Given the list of nested members and frames tuples, construct a dictionary
    with member keys and list of frames values for constructing a CSV.
        """
        self._vn = vn
        if srsref is None:
            print "WARNING: Initializing vn w/o selrestr reference!"
        self._srsref = srsref

    def stringify(self, fmt='gt-ns', verbs_only=False):
        """
        Convert verb -> frames dictionary to a string -> string dictionary
        converting frames to the specified format.

        NOTE: From recent update, f.format now returns LISTS of frames
        (all of the formats except for expanded return singleton lists), so
        we need to flatten the list at the end, and convert into a set.
        If the format is an *expanded* format (starts with e), then since each
        format call returns a LIST, not a string, an extend will be required.
        """
        vn_str = defaultdict(list)
        for verb in self._vn:
            verb_str = str(verb)
            if verbs_only:
                verb_str, _ = verb_str.split('#')

            def format_w_selrestr(f):
                return f.format(fmt=fmt, srsref=self._srsref)

            frames_str = flatten_and_unique(
                map(format_w_selrestr, self._vn[verb])
            )
            vn_str[verb_str].extend(frames_str)

        return vn_str

    def stringify_2(self, selrestrs=False, themroles=False,
                    prepliterals=False, verbs_only=False):
        """
        Second stringify for updated verbnet format.
        """
        vn_str = defaultdict(list)
        for verb in self._vn:
            verb_str = str(verb)
            if verbs_only:
                verb_str, _ = verb_str.split('#')

            def format_w_selrestr(f):
                return f.format_2(selrestrs=selrestrs,
                                  themroles=themroles,
                                  prepliterals=prepliterals,
                                  srsref=self._srsref)

            frames_str = flatten_and_unique(
                map(format_w_selrestr, self._vn[verb])
            )
            vn_str[verb_str].extend(frames_str)

        return vn_str

    def verbnet_wordnet_map(self):
        """
        Return a dictionary mapping VerbNet verbs to their WordNet ids.
        """
        return dict(verb.wn_mapping() for verb in self._vn)

    def to_csv(self, fmt='gt-ns', verbs_only=False):
        """
        Given the dict of member keys and frames lists, and the set of all
        frames present in the corpus, build a 2D list that represents a binary
        matrix with member rows and binary columns for each frame indicating
        whether the member possesses the given syntactic frame in VerbNet.

        If verbs_only is True, then no vnclasses are included in output, so
        polysemy gets collapsed.
        """
        vn_str = self.stringify(fmt=fmt, verbs_only=verbs_only)
        frames_uniq = unique_frames(vn_str)
        # Need to keep order correct
        frames = sorted(list(frames_uniq))
        # Will be used as index for pandas df
        header = ['member']
        header.extend(frames)
        mat = [header]
        for member in vn_str:
            member_frames = vn_str[member]
            # Construct the len(frames_list)-long binary row.
            row = [member]
            for frame in frames:
                # 1 - in, 0 - out
                row.append(int(frame in member_frames))
            mat.append(row)
        return mat

    def to_csv_2(self, selrestrs=None, themroles=None, prepliterals=None,
                 verbs_only=False):
        """
        Given the dict of member keys and frames lists, and the set of all
        frames present in the corpus, build a 2D list that represents a binary
        matrix with member rows and binary columns for each frame indicating
        whether the member possesses the given syntactic frame in VerbNet.

        If verbs_only is True, then no vnclasses are included in output, so
        polysemy gets collapsed.
        """
        if selrestrs is None and themroles is None and prepliterals is None:
            raise NotImplementedError("Use gt-ns format of to_csv")

        if verbs_only:
            raise NotImplementedError

        vn_str = self.stringify_2(selrestrs=selrestrs,
                                  themroles=themroles,
                                  prepliterals=prepliterals,
                                  verbs_only=verbs_only)

        frames_uniq = unique_frames(vn_str)
        # Need to keep order correct
        frames = sorted(list(frames_uniq))
        # Will be used as index for pandas df
        header = ['member']
        header.extend(frames)
        mat = [header]
        for member in vn_str:
            member_frames = vn_str[member]
            # Construct the len(frames_list)-long binary row.
            row = [member]
            for frame in frames:
                # 1 - in, 0 - out
                row.append(int(frame in member_frames))
            mat.append(row)
        return mat

    def to_pickle(fname, vn):
        # Could use JSON, maybe.
        raise NotImplementedError("Can't pickle custom classes.")

    def get_nontopic_verbs(self):
        """
        Return a list of verbs as strings only if they don't use the "topic"
        thematic role. Used for verb sampling in experiments.
        """
        nontopics = []
        for verb, framelist in self._vn.iteritems():
            # Nonthemes either?
            if not any(frame.has_tr('Topic') for frame in framelist):
                nontopics.append(str(verb))
        return nontopics
