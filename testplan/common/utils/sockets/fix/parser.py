"""
FIX messages parser.
"""


def tagsoverride(msg, override):
    """
    Merge in a series of tag overrides, with None
    signaling deletes of the original messages tags
    """
    for tag, value in override.items():
        if value is None:
            del msg[tag]
        else:
            msg[tag] = value
    return msg
