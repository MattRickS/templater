from template_resolver import exceptions


def get_regex_padding(padmin=None, padmax=None):
    """
    Gets a regex pattern for enforcing padding size on other patterns. Defaults
    to an unlimited size (minimum 1) if neither value is provided.

    Args:
        padmin (int): Minimum number of characters required
        padmax (int): Maximum number of characters allowed

    Returns:
        str: Regex padding symbol(s) to append to a regex pattern
    """
    if padmin is not None and padmax is not None:
        if padmax < padmin:
            raise exceptions.ResolverError(
                "Padmax ({}) cannot be lower than padmin ({})".format(padmax, padmin)
            )
        padding_str = "{%d,%d}" % (padmin, padmax)
    elif padmin is not None:
        padding_str = "{%d,}" % padmin
    elif padmax is not None:
        padding_str = "{,%d}" % padmax
    else:
        padding_str = "+"
    return padding_str
