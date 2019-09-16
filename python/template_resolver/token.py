import re

from template_resolver import exceptions


class Token(object):
    def __init__(self, name, regex):
        """
        Args:
            name (str): Name of the token
            regex (str): Regex pattern the token should capture
        """
        self._name = name
        self._pattern = re.compile(regex)

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

    def extract(self, string, index=0):
        """
        Attempts to extract the value from a section of the string. Does not
        have to match the full remainder of the string.

        Raises:
            exceptions.ParseError: If the string doesn't match the token

        Args:
            string (str): String to extract the token from

        Keyword Args:
            index (int): Index to start extracting from, defaults to the start
                of the string

        Returns:
            tuple[str, int]: Tuple containing the string that matches and the
                index the match finished on
        """
        match = self._pattern.match(string, index)
        if match is None:
            raise exceptions.ParseError(
                "Cannot extract {!r} from {!r} at index {}".format(
                    self._name, string, index
                )
            )
        end = match.end()
        return string[index:end], end

    def format(self, value):
        """
        Raises:
            exceptions.FormatError: If the value doesn't match the token

        Args:
            value: Token value to be formatted into a string

        Returns:
            str: Formatted value
        """
        try:
            self.parse(value)
        except exceptions.ParseError:
            raise exceptions.FormatError(
                "Value {!r} does not match {!r}".format(value, self)
            )
        return value

    def parse(self, string):
        """
        Raises:
            exceptions.ParseError: If the string doesn't match the token

        Args:
            string (str): String to parse the value from. Must match exactly.

        Returns:
            str: Parsed value
        """
        try:
            value, end = self.extract(string)
        except exceptions.ParseError:
            value, end = None, -1

        if end != len(string):
            raise exceptions.ParseError(
                "String {!r} does not match {!r}".format(string, self)
            )

        return value

    def regex(self):
        """
        Returns:
            str: String pattern representing the regex
        """
        return self._pattern.pattern


class IntToken(Token):
    def __init__(self, name, regex="[0-9]+"):
        """
        Args:
            name (str): Name of the token

        Keyword Args:
            regex (str): Regex pattern for the string. Defaults to integer
                characters only
        """
        super(IntToken, self).__init__(name, regex)

    def extract(self, string, index=0):
        """
        Attempts to extract the integer from a section of the string. Does not
        have to match the full remainder of the string.

        Raises:
            exceptions.ParseError: If the string doesn't match the token

        Args:
            string (str): String to extract the token from

        Keyword Args:
            index (int): Index to start extracting from, defaults to the start
                of the string

        Returns:
            tuple[int, int]: Tuple containing the integer that matches and the
                index the match finished on
        """
        value, end = super(IntToken, self).extract(string, index=index)
        return int(value), end

    def format(self, value):
        """
        Raises:
            exceptions.FormatError: If the value doesn't match the token

        Args:
            value (int): Integer value to be formatted into a string

        Returns:
            str: Formatted value
        """
        return super(IntToken, self).format(str(value))

    def parse(self, string):
        """
        Raises:
            exceptions.ParseError: If the string doesn't match the token

        Args:
            string (str): String to parse the value from. Must match exactly.

        Returns:
            int: Parsed integer value
        """
        value = super(IntToken, self).parse(string)
        return int(value)


class StringToken(Token):
    def __init__(self, name, regex="[a-zA-Z]+"):
        """
        Args:
            name (str): Name of the token

        Keyword Args:
            regex (str): Regex pattern for the string. Defaults to alphabetical
                characters only
        """
        super(StringToken, self).__init__(name, regex)

    def format(self, value):
        """
        Raises:
            exceptions.FormatError: If the value doesn't match the token

        Args:
            value (str): String value to be formatted into a string

        Returns:
            str: Formatted value
        """
        return super(StringToken, self).format(str(value))
