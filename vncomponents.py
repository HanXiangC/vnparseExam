"""
VN component classes. Where the bulk of the work goes.
"""


import itertools
from vnutil import pp_str_to_np_str


# See Token.is_prep_or_lexprep
LEXICAL_PREPS = [
    'as',
    'at',
    'down',  # ONLY FOR NON-TERMINAL LEX IN GOBBLE-39.3 - more filtering reqd
    'like',
]

# XXX: Remember to update this when adding to VerbNet
FORMATS = [
    'gt-ns',
    'gt-ss',
    'gt-tr',
    'cx-ns',
    'cx-ss',
    'cx-tr',
    'ex-ns',
    'ex-ss',
    'ex-tr',
    'ex-cx',
    'et-cx',
    'cx-st',
    'ex-st'
]


class Verb(object):
    def __init__(self, verb, vnclass, wn=[], grouping=None):
        self.verb = verb
        self.vnclass = vnclass
        self.wn = wn
        self.grouping = grouping

    def __str__(self):
        return '{}#{}'.format(self.verb, self.vnclass)

    def wn_mapping(self):
        return (str(self), self.wn)

    def __repr__(self):
        return self.__str__()

    def __eq__(self, other):
        return (isinstance(other, self.__class__) and
                self.verb == other.verb and
                self.vnclass == other.vnclass)

    def __ne__(self, other):
        return not self.__eq__(other)

    def __hash__(self):
        return hash((self.verb, self.vnclass))


class Pos(object):
    # Instead of int enums I use strings for helpful debugging and
    # printing
    all = ('LEX', 'NP', 'VERB', 'PREP', 'ADJ', 'ADV')
    LEX, NP, VERB, PREP, ADJ, ADV = all

    @classmethod
    def is_pos(self, s):
        return s in self.all

    def __init__(self):
        """Shouldn't be used!"""
        raise ValueError("Can't instantiate a Pos object - use Enum values!")


class TokenSelrestr(object):
    def __init__(self, selrestrs=(), logical_or=False, logical_and=False):
        """
        Init a TokenSelrestr class, used to help get literals for PPs
        primarily.

        XXX: right now, VerbNet isn't using logical_and in their XML files,
        just multiple selrestrs if those exist.
        """
        if logical_or and logical_and:
            raise ValueError("Selrestr can't have both OR and AND")
        self.selrestrs = tuple(sorted(selrestrs))
        self.logical_or = logical_or
        self.logical_and = logical_and

    def __getitem__(self, key):
        """Index into selrestrs by default."""
        return self.selrestrs[key]

    def __getslice__(self, i, j):
        return self.selrestrs[i:j]

    def __setitem__(self, key, item):
        raise ValueError("selrestrs are tuples, and not mutable")

    def __delitem__(self, key, item):
        raise ValueError("selrestrs are tuples, and not mutable")

    def __eq__(self, other):
        return (self.selrestrs == other.selrestrs and
                self.logical_or == other.logical_or and
                self.logical_and == other.logical_and)

    def __ne__(self, other):
        return not self.__eq__(other)

    def __hash__(self):
        return hash((self.selrestrs, self.logical_or, self.logical_and))

    def __nonzero__(self):
        return bool(self.selrestrs)

    def __str__(self):
        selrestrs_str = str(self.selrestrs)
        if self.logical_or:
            return 'OR' + selrestrs_str
        if self.logical_and:
            return 'AND' + selrestrs_str
        return selrestrs_str


class Token(object):
    def __init__(self, pos, value=None, selrestrs=None, synrestrs=()):
        """
        pos: a part of speech of class Pos
        value: value tag of the Pos
        theme: thematic role associated with the Pos tag
        selrestrs: any selectional restrictions on the tag, AS STRINGS
        synrestrs: any syntactical restrictions on the tag, AS STRINGS
        """
        assert not selrestrs or type(selrestrs) == TokenSelrestr
        self.assert_valid(pos, value, selrestrs, synrestrs)
        self.pos = pos
        self.value = value
        self.selrestrs = selrestrs
        # TODO: Implement synrestrs the same way?
        self.synrestrs = tuple(sorted(synrestrs))

    def assert_valid(self, pos, value, selrestrs, synrestrs):
        if pos == Pos.LEX:
            assert value and not selrestrs and not synrestrs
        elif pos == Pos.NP:
            # xor
            # FIXME: The point is that there can be a
            # synrestrs node, just that it's empty, which
            # isn't evaluated here.
            xor = ((selrestrs and not synrestrs) or
                   (synrestrs and not selrestrs)) or True
            assert value and xor
        elif pos == Pos.VERB:
            assert True  # FIXME: Anything else in this one?
        elif pos == Pos.PREP:
            assert ((value and not selrestrs) or
                  (not value and selrestrs)) and \
                 (not synrestrs)
        elif pos == Pos.ADJ:
            assert True  # FIXME: Might not be anything
        elif pos == Pos.ADV:
            assert True  # FIXME: Might not be anything
        else:
            print("line 169 vn components")
            print(pos)
            print(value)
            print(selrestrs)
            print(synrestrs)
            raise ValueError('Invalid part of speech {}'.format(pos))

    @staticmethod
    def is_pos_func(pos):
        """Return a function which returns TRUE if the Token has the given POS.
        Functional programming to mix things up."""
        assert Pos.is_pos(pos)

        return (lambda token: token.pos == pos)

    def is_prep_or_lexprep(self):
        """
        Some LEXs are treated as prepositions in VerbNet Primaries.
        We need to return those prepositions in our functions.

        Returns True if the token is either a Prep,
        or a prepositional LEX.

        FIXME: It's likely better to put something different in VerbNet
        parsing's internal classification, rather than this, but...later.
        """
        if self.pos == Pos.PREP:
            return True
        if self.pos == Pos.LEX and self.value in LEXICAL_PREPS:
            return True
        return False

    def get_prep_expansion(self, srsref=None):
        """
        Works for PREPs and LEXs, but tread carefully with LEXs. Returns a list
        that consists of every possible PP literal for the given prepositional
        phrase. It does this by two steps:

        1) if the prep has a value, it has specific preps, so return that list
        2) otherwise (as determined by assert_valid) prep as a selrestr, so
           consult [REFERENCE] to determine the necessary prepositions.
        """
        if not (self.pos == Pos.PREP or self.pos == Pos.LEX):
            raise ValueError("{} is not prep/lex".format(str(self)))
        if self.value:
            # ADDED: Ensure that there aren't duplicates. Just an extra safety
            # check.
            return list(set(self.value.split()))  # Split on whitespace
        # Assert this is a PREP and that it has a single selrestr
        assert self.pos == Pos.PREP
        if srsref is None:
            raise RuntimeError(
                "This prep has no value and no selrestr reference provided"
            )

        # This is where all the final selrestrs will be stored.
        selrestrs = set()

        # Get the literals according to the srsref.
        # So selrestr_literals should be a list of sets.
        # Use 1: to ignore +. -s dealt with separately (see below)
        def literals_or_complement(srs):
            """
            Get either the literals associated with the vprep if +, or
            everything but if -. DEPENDS ON CLASS HIERARCHY as documented in
            get_prep_literals.py, where spatial is toplevel!!!
            """
            # Trim off +/- with [1:]
            if srs.startswith('+'):
                return srsref[srs[1:]]
            else:
                assert srs.startswith('-')
                try:
                    return srsref['spatial'] - srsref[srs[1:]]
                except TypeError:
                    raise TypeError(
                        "Srsref has list vals. Convert to sets after json.load"
                    )

        selrestr_literals = map(literals_or_complement, self.selrestrs)

        if self.selrestrs.logical_or:
            # Get union of possible selrestrs
            map(lambda srs: selrestrs.update(srs), selrestr_literals)
        elif self.selrestrs.logical_and:
            # Get intersection of the selrestrs
            selrestrs = set.intersection(*selrestr_literals)
        else:
            # Otherwise there should be only one selrestr restriction,
            # so just set selrestrs to that.
            # XXX: right now, logical_and isn't being used. So ASSUME
            # AND
            if len(selrestr_literals) >= 2:
                selrestrs = set.intersection(*selrestr_literals)
            else:
                selrestrs = selrestr_literals[0]

        if not selrestrs:
            raise Exception(
                "Couldn't find literals for selrestrs {}".format(
                    self.selrestrs
                )
            )

        return list(selrestrs)

    def __eq__(self, other):
        return (isinstance(other, self.__class__) and
                self.pos == other.pos and
                self.value == other.value and
                self.selrestrs == other.selrestrs and
                self.synrestrs == other.synrestrs)

    def __ne__(self, other):
        return not self.__eq__(other)

    def __hash__(self):
        return hash(
            (self.pos, self.value, self.selrestrs, self.synrestrs)
        )

    def __str__(self):
        return "<Token: pos {}, val {}, sels {}, syns {}>".format(
            self.pos,
            self.value,
            self.selrestrs,
            self.synrestrs
        )

    def __repr__(self):
        return self.__str__()


class Themrole(object):
    def __init__(self, roletype, all_selrestrs=()):
        """
        Create a new themrole.

        NOTE: XXX: Right now, we're completely ignoring syntactic
        restrictions!

        However, if we're going to include these later on, try duplicating
        the ThemroleSelrestr class.
        """
        self.roletype = roletype
        self.all_selrestrs = tuple(sorted(all_selrestrs))

    def __eq__(self, other):
        return (isinstance(other, self.__class__) and
                self.roletype == other.roletype and
                self.all_selrestrs == other.all_selrestrs)

    def __ne__(self, other):
        return not self.__eq__(other)

    def __hash__(self):
        return hash((self.roletype, self.all_selrestrs))

    def selrestrs_strlist(self):
        """
        Return a list of all string representations of selrestrs.
        Like __str__, but doesn't join!
        """
        selrestrs = []
        for s in self.all_selrestrs:
            selrestrs.extend(s.strlist())
        return selrestrs

    def __str__(self):
        """
        NOTE: This includes roletype - we don't usually use roletype -
        make sure you're not collapsing on this!
        """
        return self.roletype + ''.join(map(str, self.all_selrestrs))

    def __repr__(self):
        return self.__str__()

    def eq_themrole(self, other):
        """
        Check if the current themrole is equal to the other themrole.
        """
        return self.roletype == other.roletype

    @staticmethod
    def merge(t1, t2):
        """
        Merge the two themeroles by combining their selectional restrictions,
        their syntactic restrictions, and returning a new themrole instance
        (which will then resort the themes)

        This function will throw an error if both themroles have different
        roletypes, so check manually or with Themrole.eq_themrole.

        20151209 TODO - merge these thematic roles in construction of
        frames and other things
        """
        if not t1.eq_themrole(t2):
            raise ValueError(
                "can't merge: t1 has roletype {}, t2 has roletype {}".format(
                    t1.roletype, t2.roletype
                )
            )
        selrestrs_combined = tuple(set(t1.all_selrestrs + t2.all_selrestrs))
        return Themrole(t1.roletype, all_selrestrs=selrestrs_combined)

    @staticmethod
    def merge_themrole_list(roles):
        """
        STATIC METHOD

        Merge duplicate roletypes in the given list of thematic roles.
        """
        # Keep track of roletypes that are already in new_roles.
        assert isinstance(roles, tuple), "List of themroles required"
        used_roletypes = set()
        # Use list for now, then convert to tuple at the end
        new_roles = []
        for r1 in roles:
            if r1.roletype in used_roletypes:  # Then we've already merged
                continue
            # This is the new themrole which will be added
            new_r = r1
            for r2 in roles:
                # If our second for loop reaches the same element, *or*
                # if there are actually identical themroles, just
                # get rid of one of them by ignoring it completely
                if r1 == r2:
                    continue
                # Otherwise, if the roletypes match, update the themrole
                # with r2's new restrictions
                if r1.roletype == r2.roletype:
                    new_r = Themrole.merge(new_r, r2)
            # Add this themrole (might be updated, might be unchanged) to
            # new_roles, and update the roletype set accordingly
            new_roles.append(new_r)
            used_roletypes.add(new_r.roletype)
        # No need to sort, will be handled by Frame()
        return tuple(new_roles)


class ThemroleSelrestr(object):
    def __init__(self, selrestrs=(), logical_or=False, logical_and=False):
        """
        Init a themrole selrestr class with support for logical_ors and ands.

        XXX: But where did the logical_ands go??
        XXX: bring-11.3 has a relevant themrole.
        """
        self.selrestrs = tuple(sorted(selrestrs))
        assert not (logical_or and logical_and)
        self.logical_or = logical_or
        self.logical_and = logical_and

    def __eq__(self, other):
        return (isinstance(other, self.__class__) and
                self.selrestrs == other.selrestrs and
                self.logical_or == other.logical_or and
                self.logical_and == other.logical_and)

    def __ne__(self, other):
        return not self.__eq__(other)

    def __hash__(self):
        return hash((self.selrestrs, self.logical_or, self.logical_and))

    def __str__(self):
        if self.logical_or:
            return '+OR({})'.format(''.join(self.selrestrs))
        if self.logical_and:
            return '+AND({})'.format(''.join(self.selrestrs))
        return ''.join(self.selrestrs)

    def __repr__(self):
        return self.__str__()

    def strlist(self):
        """Like __str__, but without joining"""
        if self.logical_or:
            # There should be only one logical or.
            return ['+OR({})'.format(''.join(self.selrestrs))]
        if self.logical_and:
            # There should be only one logical or.
            return ['+AND({})'.format(''.join(self.selrestrs))]
        return self.selrestrs

    def __cmp__(self, other):
        """
        Should be called in sorted. The point is to order by and first, then or
        first, then by selrestrs.
        """
        # Compare ANDs
        if self.logical_and and not other.logical_and:
            return 1
        if not self.logical_and and other.logical_and:
            return -1
        # Compare ORs
        if self.logical_or and not other.logical_or:
            return -1
        if not self.logical_or and other.logical_or:
            return 1
        # Otherwise ands/ors are equivalent and compare the selrestrs
        # themselves
        return cmp(self.selrestrs, other.selrestrs)

    def __iter__(self):
        for selrestr in self.selrestrs:
            yield selrestr


class Frame(object):
    def __init__(self, primary, tokens, roles, class_id):
        """
        Primary: List of as-is tokens in the primary attribute of the frame
        description
        Tokens: List of Token objects, one for each node in the Syntax xml tag
        Roles: List of global Themroles and their restrictions
        for the given vnclass
        """
        self.primary = primary
        self.tokens = tokens
        # TODO: Ensure uniqueness by merging duplicates
        self.roles = tuple(sorted(roles))
        # Debug info, ignore when checking equality
        # and other tests
        self.class_id = class_id

    def has_tr(self, roletype):
        """
        Return True if the Frame has the given thematic role. We use this for
        sampling verbs in experiment design later.
        """
        return any(tr.roletype == roletype for tr in self.roles)

    def get_themrole(self, roletype):
        """
        Return the thematic role that has the given type.
        Returns None if not found.
        """
        for trole in self.roles:
            if trole.roletype == roletype:
                return trole
        return None

    def find_next_np(self, tc):
        """
        Used in semantic expansion.
        TC is the current token - we're "consuming" the token list.

        NOTE: We assume the element at tc has already been accessed!

        Return a tuple:
        The first element is the first NP Token object found, and
        the second element is new tc - the index of the next NP object.

        Return (None, len(tokens)) if no token is found (so trying to index
        into tokens with tc will err). The function calling this needs to
        handle this case - maybe throw an exception?
        """
        while True:
            tc += 1
            try:
                token = self.tokens[tc]
            except IndexError:  # EAFP
                return (None, tc)
            if token.pos == Pos.NP:
                return (token, tc)

    def find_next_prep(self, tc):
        """
        Used in syntactic expansion. Operates the same as find_next_np.
        """
        while True:
            tc += 1
            try:
                token = self.tokens[tc]
            except IndexError:  # EAFP
                return (None, tc)
            if token.pos == Pos.PREP:
                return (token, tc)

    def has_pos(self, pos):
        """
        Return true if the frame has the specified Pos tag
        """
        isp = Token.is_pos_func(pos)
        return any(map(isp, self.tokens))

    def num_pos(self, pos):
        isp = Token.is_pos_func(pos)
        return sum(map(isp, self.tokens))

    def get_pos_list(self, pos):
        # Slightly more advanced
        isp = Token.is_pos_func(pos)
        return filter(isp, self.tokens)

    def get_prep_or_lexprep_list(self):
        # Use the is_prep_or_lexprep function.
        # Remember that there is (as of 20160407) one prep that will
        # seep through the cracks here.
        return filter(lambda t: t.is_prep_or_lexprep(), self.tokens)

    def _format_gt_ns(self):
        """Groundtruth."""
        return [' '.join(self.primary)]

    def _format_gt_ss(self, dotqs=False, real_primaries=None):
        """Groundtruth with semantics.
        If real_primaries is given, computation proceeds like normal with
        self.primary, but all tokens appended come from the corresponding
        real_primaries. This is used to make gt_ss add semantics to the result
        of gt_tr (theta roles), so that there are theta roles
        """
        # Intuition: obtain the standard representation. Then match
        # std with syntax nodes - we just care about adding selrestrs to
        #   1) NPs
        #   2) PPs (will have p.NP format, where NP has selrestr, but
        #           just don't expand the NP)
        #   2.5) FIXME: Seems to only be PP-Conative, PP-Trajectory,
        #        Are there others?
        #   3) S_INF, S_ING, etc. (these are NPs)
        #   4) ADVPs SOMETIMES
        # We ought to know that each time we encounter one of those in
        # std, we can look through our list, and based on ordering,
        # we'll find the right node.
        # When we finish the entire primary string, we ought to have gone
        # through the entire list of syntax tokens.
        semanticized = []
        # Tokens counter. Starts off at -1 because we increment first,
        # then look.
        tc = -1

        print "\n\nBegin processing frame {}".format(self.primary)

        if real_primaries:
            assert len(real_primaries) == len(self.primary)

        for index, p in enumerate(self.primary):
            if dotqs:
                no_dotq_p = p
            else:
                no_dotq_p = p.split('.')[0]

            if real_primaries:
                no_dotq_p = real_primaries[index]

            # FIXME: Move this skipping logic to another function?
            if not (p.startswith('NP') or p.startswith('PP') or
                    p.startswith('S') or p == 'ADVP'):
                semanticized.append(no_dotq_p)
                continue

            # There's the random case of "NP V PP.theme NP S_ING" in
            # rely-70.xml
            # For that, we'll just ignore both PP.theme AND NP.
            # There's only one frame like this anyways, so it won't
            # make a difference on how the frames are collapsed.
            if (self.primary[-3:] == ('PP.theme', 'NP', 'S_ING') and
                    (index == 2 or index == 3)):
                # 2nd and 3rd elements of this ^ frame are PP.theme and
                # NP.
                semanticized.append(no_dotq_p)
                continue

            # Keep these separate for readability
            if p == 'PP.theme':
                # Special (unique?) case where there may be a S_ING
                # following. If there is, then that following S gets
                # the qualifiers, and this one gets untouched.
                # If there's another element, and if that element is an S,
                # just append this token as is and move on to that S
                if (index != len(self.primary) - 1 and
                        self.primary[index + 1].startswith('S')):
                    semanticized.append(no_dotq_p)
                    continue

            p_selrestrs = []
            token, tc = self.find_next_np(tc)
            print "Found: ", token, tc
            if len(set(self.roles)) != len(self.roles):
                import ipdb
                ipdb.set_trace()
                #  raise Exception
            if token is None:
                # BEGIN:
                # Extra checks, hardcoded before we complain
                # TODO: Probably move this to another function

                # Special cases where there is no token but we continue
                # anyways:
                # 1) ADVP without noun phrase, just use ADVP
                # 2) NP-PRO-ARB
                if p == 'NP-PRO-ARB' or p.startswith('ADVP'):
                    semanticized.append(no_dotq_p)
                    continue
                elif p.startswith('S'):
                    print str((' '.join(self.primary), self.tokens))
                    # x = raw_input("Confirm: y/n ")
                    # assert x != 'n'
                    # import ipdb; ipdb.set_trace()
                    uniques = set(r.roletype for r in self.roles)
                    if len(uniques) != len(self.roles):
                        print self.roles
                        import ipdb
                        ipdb.set_trace()
                    semanticized.append(no_dotq_p)
                    continue
                    # TODO XXX FIXME NOTE
                    # Duplicate roles can occur when subclass roles
                    # are added to the list of roles.
                    # Example: two co-patients
                    # Roles ['Patient', 'Agent+OR(+animate+machine)',
                    # 'Co-Patient', 'Co-Patient+OR(+abstract+animate)',
                    # 'Patient+concrete', 'Agent+OR(+abstract+animate)']
                    # Let this run, confirming everything, until errors
                    # like ^ happen.
                elif p == 'PP.attribute':
                    # Check this - consider-29.9 NP V NP PP.attribute
                    # only has two NPs, so no need to differentiate.
                    semanticized.append(no_dotq_p)
                    continue
                # Hardcoded exceptions to token mismatches
                elif ' '.join(self.primary) in [
                        # mix-22.1.xml NP NP V together, NP V NP NP
                        # together
                        # More evidence that we need synrestrs, as the
                        # first two NPs are just collapsed into one
                        # NP+plural.
                        'NP NP V together',
                        'NP V NP NP together',
                        'NP NP V ADVP-Middle together',
                        'NP V NP to be NP']:  # confess-37, indicate-78
                    semanticized.append(no_dotq_p)
                    continue
                elif 'PP.topic' in self.primary:
                    # Some PP.topics, and maybe other PPs, have
                    # Ss that "disappear"
                    # just check that the last token is an NP
                    # and has a synrestr
                    last = self.tokens[-1]
                    assert last.pos == 'NP' and last.synrestrs
                    print "Warning: skipping {} for {}".format(
                        p, ' '.join(self.primary)
                    )
                    semanticized.append(no_dotq_p)
                    continue
                else:
                    continue
            # Get TOKEN selrestrs which are STRINGS
            p_selrestrs.extend(token.selrestrs)
            # Check if the corresponding toplevel thematic role
            # has any selrestrs, and add them to our list
            token_role = token.value
            themrole = self.get_themrole(token_role)
            print themrole
            if not themrole:
                continue
            p_selrestrs.extend(themrole.selrestrs_strlist())
            # Collapse into unique and sort
            ps_uniq_sort = sorted(set(p_selrestrs))
            # Add the selrestrs to the token
            no_dotq_p += ''.join(ps_uniq_sort)
            semanticized.append(no_dotq_p)
            # We should have consumed the entire list.
            # This isn't going to work - doesn't always end with PPs
        print "TC", tc
        print "Tokens", self.tokens
        print "Old", self.primary
        print "New", semanticized
        print "Roles", map(str, self.roles)
        if tc != len(self.tokens) - 1:  # Just ask for confirmation
            pass
            # x = raw_input("Good? y/n ")
            # assert x != 'n'
        print "Good!"
        return [' '.join(semanticized)]

    def _format_gt_tr(self, primaries=None):
        """
        Groundtruth, theta roles.

        This function specifically accepts an extra primaries argument -
        will be used in cx_tr

        XXX: While it is likely good practice to put the optional primaries
        argument for all theta roles, that will take a while, so I will just
        add the optinal arguments as needed
        """
        semanticized = []

        if primaries is None:
            primaries = self.primary
        tc = -1  # Token count
        for index, p in enumerate(primaries):
            if not (p.startswith('NP') or p.startswith('PP') or
                    p.startswith('S') or p == 'ADVP'):
                semanticized.append(p)
                continue

            token, tc = self.find_next_np(tc)
            if token is None:
                # Deal with some special issues before failing.
                # Sentential complements:
                if p.startswith('S_') and 'PP.' in primaries[index - 1]:
                    # If sentential complement and the previous preposition
                    # is dotqed, just attach on the sentential complement;
                    # the preposition has the theta role
                    semanticized.append(p)
                    continue

                # If already dotqed. Set maximum lookback to -2
                if any('.' in prev for prev in semanticized[-2:]):
                    semanticized.append(p)
                    continue

                # NP V NP to be NP
                # no theta role for the last NP. So NP.theta V NP.theta
                if (len(semanticized) >= 3 and
                        semanticized[-2:] == ['to', 'be'] and
                        '.' in semanticized[-3]):
                    semanticized.append(p)
                    continue

                if ' '.join(primaries) in [
                        'NP NP V together',
                        'NP V NP NP together',
                        'NP NP V ADVP-Middle together',
                        'NP NP V ADVP together',  # CX variant of mix
                        'NP V NP to be NP']:
                    semanticized.append(p)
                    continue

                print "Primary", primaries
                print "Tokens", self.tokens
                print "Semanticized", semanticized
                import ipdb
                ipdb.set_trace()
            val = token.value.lower()
            if val in p.lower():
                # Then the NP/PP/what have you is already qualified, so just
                # append the original token
                # TODO: check to see proper capitalization
                # Like NP-Agent -> NP.agent
                semanticized.append(p)
            else:
                dotqed = '{}.{}'.format(p, val)
                semanticized.append(dotqed)

            #  If we've somehow added TWO dotqs, not good!
            #  if len(semanticized[-1].split('.')) >= 3:
                #  print "Primary", primaries
                #  print "Tokens", self.tokens
                #  print "Semanticized", semanticized
                #  if raw_input("Good?: ").lower() != 'y':
                #     import ipdb
                #     ipdb.set_trace()

        if len(primaries) != len(semanticized):
            print "Primary", primaries
            print "Tokens", self.tokens
            print "Semanticized", semanticized
            if raw_input("Good?: ").lower() != 'y':
                import ipdb
                ipdb.set_trace()
        return [' '.join(semanticized)]

    def _format_cx_ns(self):
        """Collapsed, no semantics."""
        # For each POS tag in a verb frame, remove any dot qualifiers.
        collapsed = map(remove_ptoken_syntax, self.primary)
        return [' '.join(collapse_extra(collapsed))]

    def _format_cx_ss(self):
        """Collapsed with semantics."""
        # Use gt-ss to prevent having to copy everything over. Split on
        # whitespace again.
        # gt-ss only returns one frame
        tokens_ss = self.format(fmt='gt-ss')[0].split()
        tokens_cx = []
        for token in tokens_ss:
            # To reobtain the token without the selectional restrictions,
            # we use good old string iteration up until a + or a -
            # (signalling the start of selrestrs)
            # This is the most unpythonic thing I've ever written
            stem = ""
            stem_done = False
            restrs = ""
            for char in token:
                if char == '+' or char == '-':
                    # Selrestr found, stop adding to stem
                    stem_done = True
                if stem_done:
                    # When stem is finished, add to restrictions
                    restrs += char
                    continue
                stem += char
            assert stem, 'No token stem found for {}'.format(token)
            # Get rid of stem syntax but keep selectional restrictions
            tokens_cx.append(remove_ptoken_syntax(stem) + restrs)
        return [' '.join(tokens_cx)]

    def _format_cx_tr(self):
        """Collapsed, theta roles."""
        # Get the collapsed version then go through the same theta-role adding
        # process
        tokens_cx = self.format('cx-ns')[0].split()
        return self._format_gt_tr(primaries=tokens_cx)

    def _format_ex_ns(self, srsref=None, primaries=None):
        """
        Expanded by preposition, no semantics.

        Accepts a list of primaries to use instead of self.primaries, which is
        useful for ex-ss and ex-tr.
        """
        if primaries is None:
            primaries = self.primary

        pps = self.get_prep_or_lexprep_list()

        # We only expand tokens with prepositions, so just
        # return the standard groundtruth format in a singleton list
        if len(pps) == 0 or \
                (len(self.primary) == 1 and self.primary[0] == 'Passive'):
            # Ignore passive frames or frames with no preps
            # Don't use gt-ns, just join the primaries
            return [' '.join(primaries)]

        expanded = []
        pp_literals = [pp.get_prep_expansion(srsref) for pp in pps]
        # To optimize but sacrifice debug, feel free to remove list()
        literals_product = list(itertools.product(*pp_literals))
        # Create a NEW syntactic subframe for each of these literal products.
        for literalp in literals_product:
            subframe = []
            literal_i = 0  # Start at the beginning of the literalp tuple
            for index, p in enumerate(primaries):
                if not p.startswith('PP'):
                    # SOMETIMES verbnet has literals in the primary frame. So
                    # we do that check, and if the primary token matches the
                    # next literal token, skip that literal
                    # XXX: Is this foolproof? Can we be possibly skipping
                    # something?
                    if (literal_i < len(literalp) and     # Only if there are
                            (p == literalp[literal_i])):  # still literals
                        literal_i += 1
                    subframe.append(p)
                else:
                    # Replace with literal instead, and convert PP into NP
                    subframe.append(literalp[literal_i - 1])
                    subframe.append(pp_str_to_np_str(p))
                    literal_i += 1
            # At the end, if we haven't used all the PP literals, deal with
            # exceptions
            # Remember we incr after each access, so if we access last element
            # in e.g. 2 element list @ index 1, literalp should be 2
            if literal_i < len(literalp):
                # Exceptions
                if literalp[literal_i] == u'as' and \
                        'PP' not in ' '.join(primaries):
                    # Or insert an "as" second-to-last thing?
                    pass
                elif subframe[-1].startswith('S') and \
                        literal_i == len(literalp) - 1:
                    # Then penultimate is literal, so add BEFORE
                    if subframe[-2].islower():
                        subframe.insert(-2, literalp[literal_i])
                    else:
                        subframe.insert(-1, literalp[literal_i])
                    print "literals_product", literals_product
                    print "Subframe", subframe
                    print "Primary", primaries
                    print "Tokens", self.tokens
                    print "vnclass", self.class_id
                    #  if (raw_input("Good? ").lower() != 'y'):
                    #      raise AssertionError
                else:
                    print "literals_product", literals_product
                    print "Subframe", subframe
                    print "Primary", primaries
                    print "Tokens", self.tokens
                    print "vnclass", self.class_id
                    import ipdb;
                    expanded.append(' '.join(subframe))
        return expanded
        # TODO: Iterate through primary, or iterate through
        # tokens, or get a find_next method for PP too?
        # Probably get a find next method for PP, probably get...
        # The problem is, this format needs to happen immediately.
        # We can't do much waiting. So, we should, while parsing verbnet,
        # begin collecting those DOTqs we see. TAKE INTO ACCOUNT - and . sa
        # well
        # Will cause pain: correspond-36.1.xml
        # NP V PP.co-agent PP.theme whether S_INF

    def _format_ex_ss(self, srsref=None):
        """Expanded by preposition, semantics."""
        # Add semantic information to the semanticized primaries from
        # gt_ss, rather than the normal self.primaries.
        # Remember _format_gt_ss returns a singleton list, with the joined
        # frames.
        semantic_primaries = self._format_gt_ss()[0].split()
        return self._format_ex_ns(srsref=srsref, primaries=semantic_primaries)

    def _format_ex_tr(self, srsref=None):
        """Expanded by preposition, theta roles."""
        # Same intution, but for Theta Roles.
        tr_primaries = self._format_gt_tr()[0].split()
        return self._format_ex_ns(srsref=srsref, primaries=tr_primaries)

    def _format_ex_cx(self, srsref=None):
        """
        Expanded + collapsed. Taking ex-ns parsing but then *removing*
        dotqualifiers and other semantics.
        """
        # Idea: obtain base ex-ns, then remove dotqualifiers similar to cx
        ex_primaries = map(
            lambda f: f.split(),
            self._format_ex_ns(srsref=srsref)
        )
        # We don't exactly replicate cx, because we don't need the
        # collapse_extra method; the collapse_extra method explicitly condenses
        # prepositions into Pos tags that we've just expanded
        # remove ptoken syntax operates on a single string token, so nest
        # map calls
        # XXX: Are there duplicates here? Do I check for duplicates elsewhere?
        # I'll re-check here just for safety, since it's been a while
        collapsed_ex = map(
            lambda lst: ' '.join(map(remove_ptoken_syntax, lst)),
            ex_primaries
        )
        return list(set(collapsed_ex))

    def _format_et_cx(self, srsref=None):
        """
        Expanded with THETA ROLES + collapsed by removing dot qualifiers.
        """
        # Idea: obtain base ex-ns, then remove dotqualifiers similar to cx
        # Get the expanded/collapsed version, then go through the same
        # theta-role adding process
        ex_cx_primaries = map(
            lambda f: f.split(),
            self._format_ex_cx(srsref=srsref)
        )
        et_cx = map(
            # Remember gt_tr, like all other format functions, gives a
            # singleton list, so I grab the first element
            lambda p: self._format_gt_tr(primaries=p)[0],
            ex_cx_primaries
        )
        return list(set(et_cx))

    def _format_cx_st(self):
        """Collapsed, theta roles + selectional restrictions"""
        # Get theta roles first. Then add selectional restrictions.
        # Then collapse extra prepositions.
        tokens_tr = self._format_gt_tr()[0].split()
        tokens_tr_ss = self._format_gt_ss(dotqs=True,
                                          real_primaries=tokens_tr)
        return [' '.join(collapse_extra(tokens_tr_ss))]

    def _format_ex_st(self, srsref=None):
        """Expanded, theta roles + selectional restrictions"""
        # Get theta roles first. Then add selectional restrictions.
        # Then expand
        tokens_tr = self._format_gt_tr()[0].split()
        tokens_tr_ss = self._format_gt_ss(dotqs=True,
                                          real_primaries=tokens_tr)
        tokens_tr_ss = tokens_tr_ss[0].split()
        return self._format_ex_ns(srsref=srsref, primaries=tokens_tr_ss)

    def format(self, fmt='gt-ns', srsref=None):
        """
        Checking for equality based on various syntactic restrictions
        can be done by calling the format function with various
        specifications according to the frames requested.
        """
        if fmt == 'gt-ns':
            return self._format_gt_ns()
        elif fmt == 'gt-ss':
            return self._format_gt_ss()
        elif fmt == 'gt-tr':
            return self._format_gt_tr()
        elif fmt == 'cx-ns':
            return self._format_cx_ns()
        elif fmt == 'cx-ss':
            return self._format_cx_ss()
        elif fmt == 'cx-tr':
            return self._format_cx_tr()
        elif fmt == 'ex-ns':
            return self._format_ex_ns(srsref=srsref)
        elif fmt == 'ex-ss':
            return self._format_ex_ss(srsref=srsref)
        elif fmt == 'ex-tr':
            return self._format_ex_tr(srsref=srsref)
        elif fmt == 'ex-cx':
            return self._format_ex_cx(srsref=srsref)
        elif fmt == 'et-cx':
            return self._format_et_cx(srsref=srsref)
        elif fmt == 'cx-st':
            return self._format_cx_st()
        elif fmt == 'ex-st':
            return self._format_ex_st(srsref=srsref)
        else:
            raise ValueError('Unknown format {}'.format(fmt))

    def format_2(self, selrestrs=None, themroles=None,
                 prepliterals=None, srsref=None):
        """
        Second version of format function to correspond with new syntax.
        """
        # Otherwise, all format options should be specified
        assert (type(selrestrs) == bool and
                type(themroles) == bool and
                type(prepliterals) == bool), "Supply all boolean properties"
        return [''.join(map(str, map(int, [selrestrs, themroles, prepliterals])))]

    def __str__(self):
        """
        Default as-is primary description.
        """
        return self.format(fmt='gt-ns')

    def __repr__(self):
        return "Frame [Primary: {}, Tokens: {}, Roles: {}]".format(
            str(self.primary), str(self.tokens), str(self.roles)
        )

    def __eq__(self, other):
        """
        A very strict definition of equality - primary tokens and
        syntactic tokens must be equal. Collapsing needs to be done in
        other functions.
        """
        return (isinstance(other, self.__class__) and
                self.primary == other.primary and
                self.tokens == other.tokens and
                self.roles == other.roles)

    def __ne__(self, other):
        return not self.__eq__(other)

    def __hash__(self):
        return hash((self.primary, self.tokens, self.roles))


def remove_ptoken_syntax(ptoken):
    """
    Remove extra syntax from a single primary verb token. Look at
    functions defined within to see what is being stripped.

    Because this function operates on primary tokens, and not the
    syntactic tokens of the function, and the function operates regardles
    of frame format, the function is defined as a toplevel static method.
    """
    def remove_dotq(ptoken):
        """
        This function checks if the word contains a . division
        by splitting. If it does, we return only the first part.

        NOTE: The assumption of this code is that there is only ever
        one dot division. If this isn't the case, rewrite!
        """
        splits = ptoken.split('.')
        assert not (len(splits) > 2), \
            "This ptoken has more than one dot:\n {}".format(ptoken)
        if len(splits) > 1:
            return splits[0]
        return ptoken  # Otherwise, leave ptoken alone

    def remove_underscore(ptoken):
        """
        This function changes sentential complements
        S_ING
        S_INF
        etc.

        to just
        S
        """
        # Ignore lowercase prepositions
        if ptoken.islower():
            return ptoken

        splits = ptoken.split('_')

        if len(splits) > 2:
            raise ValueError(
                "This ptoken has more than one underscore:\n {}".format(ptoken)
            )
        if len(splits) > 1:
            return splits[0]
        return ptoken

    def remove_dash(ptoken):
        """Remove dash qualifiers like
        ADV-Middle
        NP-Conative
        S-Quote
        to just
        ADV
        NP
        S

        Q: What's the difference between -, _, . qualifications?
        """
        splits = ptoken.split('-')
        # In this case, there can be more than one dash.
        # See: NP-ATTR-POS, NP-PRO-ARB.
        # We'll get rid of all of the dashes with the same method as before.
        if len(splits) > 1:
            return splits[0]
        return ptoken

    # Order may matter. First remove dots, then underscores, then dashes
    return remove_dash(remove_underscore(remove_dotq(ptoken)))


def collapse_extra(ptoken_list):
    """
    To construct CX lists, some additional frames need to be collapsed further.
    XXX: In v3.2 (2013), contribute-13.2, future_having-13.3

    While making this function, try to order checks from least time-consuming
    to most time-consuming (but keep track of dependencies too).
    """
    length = len(ptoken_list)

    if ptoken_list == ['NP', 'V', 'for', 'NP', 'S']:
        return ['NP', 'V', 'PP', 'S']

    # NP V ... {what,whether,if,...} S -> NP V ... comp S
    if length > 1 and ptoken_list[-1] == 'S' and ptoken_list[-2].islower():
        ptoken_list[-2] = 'comp'
        return ptoken_list

    # NP VP that S PP -> NP VP comp S PP
    if (length > 2 and ptoken_list[-2:] == ['S', 'PP'] and
            ptoken_list[-3].islower()):
        ptoken_list[-3] = 'comp'
        return ptoken_list

    # NP V {down,for} NP -> NP V PP
    # This is a good place to optimize, if I ever need to.
    if ptoken_list in (['NP', 'V', 'down', 'NP'],
                       ['NP', 'V', 'for', 'NP'],
                       ['NP', 'V', 'up', 'NP']):
        return ['NP', 'V', 'PP']

    # No changes
    return ptoken_list
