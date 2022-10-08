class FormatError(Exception):
    """Errors with formatting values into strings"""


class MissingTokenError(FormatError):
    """Errors with missing token fields"""

    def __init__(self, token_name):
        super(MissingTokenError, self).__init__(f"Missing required token: {token_name}")
        self.token_name = token_name


class ParseError(Exception):
    """Errors with parsing a string into values"""


class ResolverError(Exception):
    """Errors raised with the TemplateResolver construction"""


class DebugParseError(ParseError):
    """Debug error for more accurate error reporting"""

    def __init__(self, message, char_index, segment_index, partial_fields):
        """
        Args:
            message (str): Error message
            char_index (int): Index of the string where the template stops matching
            segment_index (int): Index for the segment in the template that failed
            partial_fields (dict): Dictionary of the fields matching so far
        """
        super(DebugParseError, self).__init__(message)
        self.char_index = char_index
        self.segment_index = segment_index
        self.fields = partial_fields


class MismatchTokenError(DebugParseError):
    """Debug error for two tokens who match different values"""


class ExcessStringError(DebugParseError):
    """Debug error for when a template matches but the whole string is not consumed"""
