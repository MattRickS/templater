class FormatError(Exception):
    """ Errors with formatting values into strings """


class ParseError(Exception):
    """ Errors with parsing a string into values """


class TokenConflictError(ParseError):
    """ Error raised when multiple tokens conflict """

    def __init__(self, token_name, values):
        super(TokenConflictError, self).__init__(
            "Mismatched values found for {!r}: {}".format(token_name, values)
        )
        self.token_name = token_name
        self.values = values
