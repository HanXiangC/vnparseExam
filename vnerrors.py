"""
VerbNet has some naming, syntax, and other discrepancies.

To make the running list of errors as explicit as possible, I'm
putting as much of the error correction functionality into this
module as I can. Then, these functions will be used in other modules.
"""


def correct_frame(frame, class_id=None):
    """
    Some VN frames have minor issues, where they should (presumably) be the
    same thing.

    Need to double check on these with whoever.

    class_id is optional since sometimes we don't have that information
    (get_frame_literals.py). So we proceed conservatively and reject frame changes
    if class_id is None
    """
    if frame == 'NP v':
        return 'NP V'
    elif frame == 'NP V NP-dative NP':
        return 'NP V NP-Dative NP'
    elif frame == 'NP V NP P.asset':  # build-26.1
        return 'NP V NP PP.asset'
    elif frame == 'PP.location V PP.theme':  # swarm-47.5-1-1
        # PP.location should be NP. Syntax for the frame says so
        return 'NP.location V PP.theme'
    elif frame == 'NP V PP.theme NP.location':
        # CONTROVERSIAL: make it NP V PP.location PP.theme
        # See examples search-35.2
        return 'NP V PP.theme PP.location'
    elif frame == 'NP V NP PP.source NP.asset':
        # semi-controversial: see get-13.5.1
        # seems like it should be NP V NP PP.source PP.asset since it's
        # clearly an "at" at the end of that PREP..
        # Won't make a big difference anyways insofar as it's the only verb
        # with this frame
        return 'NP V NP PP.source PP.asset'
    elif frame == 'NP.location V NP' and \
            class_id == u'entity_specific_modes_being-47.2':
        # See np.location v np for entity_specific_modes_being-47.2
        # and ONLY for entity...this one has a PREP in syntax but no
        # prep for fit-54.3 (equivalent theme)
        # Also, PP.location V NP is actually a frame! Appears in a lot of
        # other places
        return 'PP.location V NP'
    elif frame == 'NP.location V NP.theme' and \
            class_id == 'sound_existence-47.4':
        # See corresponding class id. There are many NP.location V PP.themes,
        # very few NP.location V NP.themes. This particular frame seems
        # indistinguishable from NP.location V PP.theme in sound_emission,
        # for example.
        return 'NP.location V PP.theme'
    # What is disappearance-48.2 There V PP NP???

    #  if class_id == 'entity_specific_modes_being-47.2':
        #  import ipdb; ipdb.set_trace()

    # Nothing wrong!
    return frame

# Maybe errors:
# Some frames have initial_loc vs initial_location, I correct that when
# parsing


def correct_wn_synset(frame):
    """
    Used in vnwn_to_sim.py
    Some wn_synsets have ? in front of them. Probably means uncertainty. But
    we're going to go ahead and go with that synset...
    """
    # Was going to keep track of ?s manually, but there are too many, so I'm
    # going to do a generic .startswith(?)
    if frame.startswith('?'):
        return frame[1:]
    if frame == 'moult%2:39:00':
        # No synset found??
        # Found corrected one by checking WN browser - molt is a synonym of
        # shed. This seems to be a bug
        return 'molt%2:29:00'
    return frame
