import re

from template_resolver import exceptions


class Token(object):
    def __init__(self, name, regex, format_string=None):
        """
        Args:
            name (str): Name of the token
            regex (str): Regex pattern the token should capture
            format_string (str): Python format string to use when formatting
        """
        self._name = name
        self._pattern = re.compile("^{}$".format(regex))
        self._format_string = format_string or ""

    def __repr__(self):
        return "{s.__class__.__name__}({s.name!r}, {regex!r})".format(
            s=self, regex=self.regex()
        )

    def __str__(self):
        return self._name

    @property
    def name(self):
        """
        Returns:
            str: Name of the token
        """
        return self._name

    @property
    def format_string(self):
        """
        Returns:
            str: Python format string for the token
        """
        return self._format_string

    def format(self, value):
        """
        Raises:
            exceptions.FormatError: If the value doesn't match the token

        Args:
            value: Token value to be formatted into a string

        Returns:
            str: Formatted value
        """
        formatter = "{:%s}" % self._format_string
        try:
            string = formatter.format(value)
        except ValueError:
            raise exceptions.FormatError(
                "Value {!r} does not match {!r}".format(value, self)
            )

        try:
            self.parse(string)
        except exceptions.ParseError:
            raise exceptions.FormatError(
                "Value {!r} does not match {!r}".format(value, self)
            )
        return string

    def parse(self, string):
        """
        Raises:
            exceptions.ParseError: If the string doesn't match the token

        Args:
            string (str): String to parse the value from. Must match exactly.

        Returns:
            str: Parsed value
        """
        matched = self._pattern.match(string)
        if matched is None:
            raise exceptions.ParseError(
                "String '{}' does not match token '{}'".format(string, self._name)
            )

        value = self.to_value(string)
        return value

    def regex(self):
        """
        Returns:
            str: String pattern representing the regex
        """
        return self._pattern.pattern[1:-1]

    def to_value(self, string):
        """
        Args:
            string (str): String to be converted to the token's value

        Returns:
            str:
        """
        return string


class IntToken(Token):
    def __init__(self, name, regex="[0-9]+", format_string=None):
        """
        Args:
            name (str): Name of the token

        Keyword Args:
            regex (str): Regex pattern for the string. Defaults to integer
                characters only
            format_string (str): Python format string to use when formatting,
                should not include the 'd' for integer

        """
        super(IntToken, self).__init__(
            name, regex, format_string=(format_string or "") + "d"
        )

    def to_value(self, string):
        """
        Args:
            string (str): String value

        Returns:
            int: Integer value
        """
        try:
            return int(string)
        except ValueError:
            raise exceptions.ParseError(
                "String '{}' does not match int token '{}'".format(string, self._name)
            )


class StringToken(Token):
    """ Token representing alphabetic characters only """

    def __init__(self, name, regex="[a-zA-Z]+", format_string=None):
        """
        Args:
            name (str): Name of the token

        Keyword Args:
            regex (str): Regex pattern for the string. Defaults to alphabetical
                characters only
        """
        super(StringToken, self).__init__(
            name, regex, format_string=(format_string or "") + "s"
        )
