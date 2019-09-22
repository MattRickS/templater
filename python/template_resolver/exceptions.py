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


class ResolverError(Exception):
    """ Errors raised with the TemplateResolver construction """
