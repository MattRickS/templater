from typing import TYPE_CHECKING

from templater import constants, exceptions

if TYPE_CHECKING:
    from templater.template import Template


def format_string_debugger(
    template: "Template", string: str, debug_exc: exceptions.DebugParseError
) -> str:
    """
    Args:
        template: Template that raised the error
        string: String that failed to parse
        debug_exc: Exception raised during debugging

    Returns:
        Formatted error message that pinpoints the error
    """
    segments = template.segments()
    if debug_exc.segment_index >= len(segments):
        validate_message = [str(debug_exc)]
    else:
        segment = segments[debug_exc.segment_index]
        validate_message = [
            f"String '{segment}' does not match"
            if isinstance(segment, str)
            else f"Token '{segment.name}' does not match: {segment.description}"
        ]
    prefix_string = "Pattern: "
    indent = len(prefix_string)
    validate_message.append(f"{prefix_string}{template.pattern()}")
    validate_message.append(" " * indent + string)
    validate_message.append(" " * (indent + debug_exc.char_index) + "^")
    return "\n".join(validate_message)


def get_case_regex(case: str) -> str:
    """
    Args:
        case: Name of the case to construct a regex for

    Returns:
        Regex pattern for parsing the case - does not include padding
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
        raise exceptions.ResolverError(f"Unknown case: {case}")

    return regex


def get_regex_padding(padmin: int = None, padmax: int = None) -> str:
    """
    Gets a regex pattern for enforcing padding size on other patterns. Defaults
    to an unlimited size (minimum 1) if neither value is provided.

    Args:
        padmin: Minimum number of characters required
        padmax: Maximum number of characters allowed

    Returns:
        Regex padding symbol(s) to append to a regex pattern
    """
    if padmin is not None and padmin < 0:
        raise exceptions.ResolverError(f"Padmin cannot be less than 0: {padmin}")
    if padmax is not None and padmax < 0:
        raise exceptions.ResolverError(f"Padmax cannot be less than 0: {padmax}")

    if padmin is not None and padmax is not None:
        if padmax < padmin:
            raise exceptions.ResolverError(
                f"Padmax ({padmax}) cannot be lower than padmin ({padmin})"
            )
        padding_str = "{%d,%d}" % (padmin, padmax)
    elif padmin is not None:
        padding_str = "{%d,}" % padmin
    elif padmax is not None:
        padding_str = "{,%d}" % padmax
    else:
        padding_str = "+"
    return padding_str
