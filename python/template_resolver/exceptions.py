class FormatError(Exception):
    """ Errors with formatting values into strings """


class MissingTokenError(FormatError):
    """ Errors with missing token fields """

    def __init__(self, token_name):
        super(MissingTokenError, self).__init__(
            "Missing required token: {}".format(token_name)
        )
        self.token_name = token_name


class ParseError(Exception):
    """ Errors with parsing a string into values """


class TokenConflictError(ParseError):
    """ Errors raised when multiple tokens conflict """

    def __init__(self, token_name, values):
        super(TokenConflictError, self).__init__(
            "Mismatched values found for {!r}: {}".format(token_name, values)
        )
        self.token_name = token_name
        self.values = values
