import six

from templater import constants, exceptions


def format_string_debugger(template, string, debug_exc):
    """
    Args:
        template (templater.template.Template): Template that raised the
            error
        string (str): String that failed to parse
        debug_exc (exceptions.DebugParseError): Exception raised during
            debugging

    Returns:
        str: Formatted error message that pinpoints the error
    """
    segments = template.segments()
    if debug_exc.segment_index >= len(segments):
        validate_message = [str(debug_exc)]
    else:
        segment = segments[debug_exc.segment_index]
        validate_message = [
            "String '{}' does not match".format(segment)
            if isinstance(segment, six.string_types)
            else "Token '{}' does not match: {}".format(
                segment.name, segment.description
            )
        ]
    prefix_string = "Pattern: "
    indent = len(prefix_string)
    validate_message.append("{}{}".format(prefix_string, template.pattern()))
    validate_message.append(" " * indent + string)
    validate_message.append(" " * (indent + debug_exc.char_index) + "^")
    return "\n".join(validate_message)


def get_case_regex(case):
    """
    Args:
        case (str): Name of the case to construct a regex for

    Returns:
        str: Regex pattern for parsing the case - does not include padding
    """
    if case == constants.Case.Lower:
        regex = "[a-z]"
    elif case == constants.Case.LowerCamel:
        regex = "[a-z][a-zA-Z]"
    elif case == constants.Case.Upper:
        regex = "[A-Z]"
    elif case == constants.Case.UpperCamel:
        regex = "[A-Z][a-zA-Z]"
    else:
        raise exceptions.ResolverError("Unknown case: {}".format(case))

    return regex


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
    if padmin is not None and padmin < 0:
        raise exceptions.ResolverError(
            "Padmin cannot be less than 0: {}".format(padmin)
        )
    if padmax is not None and padmax < 0:
        raise exceptions.ResolverError(
            "Padmax cannot be less than 0: {}".format(padmax)
        )

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
