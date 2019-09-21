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
        padding_str = "{%d,%d}" % (padmin, padmax)
    elif padmin is not None:
        padding_str = "{%d,}" % padmin
    elif padmax is not None:
        padding_str = "{,%d}" % padmax
    else:
        padding_str = "+"
    return padding_str


def get_format_spec(padchar, padalign, padmin):
    """
    Args:
        padchar (str): Symbol to pad with
        padalign (str): Symbol to use for alignment
        padmin (int): minimum number of characters required

    Returns:
        str: Python format spec
    """
    return "{}{}{}".format(padchar, padalign, padmin)
