import re

from template_resolver import constants, exceptions, util


class Token(object):
    PADALIGN = ">"
    PADCHAR = "0"
    REGEX = "."

    @classmethod
    def get_format_spec_from_config(cls, config):
        """
        Args:
            config (dict): Dictionary of token configuration values

        Returns:
            str: Format spec for the token
        """
        format_spec = config.get("format_spec")
        if format_spec is None:
            padmin = config.get("padmin")
            if padmin is None:
                format_spec = ""
            else:
                padalign = config.get("padalign", cls.PADALIGN)
                padchar = config.get("padchar", cls.PADCHAR)
                format_spec = "".join((padchar, padalign, str(padmin)))

        return format_spec

    @classmethod
    def get_regex_from_config(cls, config):
        """
        Args:
            config (dict): Dictionary of token configuration values

        Returns:
            str: Regex pattern for the token
        """
        regex = config.get("regex")
        choices = config.get("choices")
        padmin = config.get("padmin")
        padmax = config.get("padmax")
        if regex is None:
            if choices:
                regex = "|".join(map(str, choices))
            else:
                regex = cls.REGEX
                regex += util.get_regex_padding(padmin=padmin, padmax=padmax)
        elif choices or padmin or padmax:
            raise exceptions.ResolverError(
                "Cannot use construction keywords with explicit regex"
            )

        return regex

    def __init__(self, name, regex, format_spec, description=None):
        """
        Args:
            name (str): Name of the token
            regex (str): Regex pattern the token should capture
            format_spec (str): Python format string to use when formatting

        Keyword Args:
            description (str): Description for the token. Used to explain how
                the value should be formatted
        """
        self._name = name
        self._pattern = re.compile("^{}$".format(regex))
        self._format_spec = format_spec
        self._description = description or ''

    def __repr__(self):
        return (
            "{s.__class__.__name__}({s.name!r}, {regex!r}, {s.format_spec!r}, "
            "description={s.description!r})".format(s=self, regex=self.regex())
        )

    def __str__(self):
        return self._name

    @property
    def description(self):
        """
        Returns:
            str: Description message to display for the token
        """
        return self._description

    @property
    def name(self):
        """
        Returns:
            str: Name of the token
        """
        return self._name

    @property
    def format_spec(self):
        """
        Returns:
            str: Python format spec for the token
        """
        return self._format_spec

    def format(self, value):
        """
        Raises:
            exceptions.FormatError: If the value doesn't match the token

        Args:
            value: Token value to be formatted into a string

        Returns:
            str: Formatted value
        """
        formatter = "{:%s}" % self._format_spec
        try:
            string = formatter.format(value)
        except ValueError:
            raise exceptions.FormatError(
                "Value {!r} does not match {!r}".format(value, self)
            )

        try:
            self.parse(string)
        except (ValueError, exceptions.ParseError):
            raise exceptions.FormatError(
                "Value as string {!r} does not match {!r}".format(string, self)
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
                "String '{}' does not match token {!r}".format(string, self)
            )

        value = self.value_from_parsed_string(string)
        return value

    def regex(self):
        """
        Returns:
            str: String pattern representing the regex
        """
        return self._pattern.pattern[1:-1]

    def value_from_parsed_string(self, string):
        """
        Args:
            string (str): String to be converted to the token's value

        Returns:
            str:
        """
        return string


class IntToken(Token):
    PADALIGN = constants.DEFAULT_PADALIGN_INT
    PADCHAR = constants.DEFAULT_PADCHAR_INT
    REGEX = constants.REGEX_INT

    @classmethod
    def get_format_spec_from_config(cls, config):
        """
        Args:
            config (dict): Dictionary of token configuration values

        Returns:
            str: Format spec for the token with the integer "d" appended
        """
        format_spec = super(IntToken, cls).get_format_spec_from_config(config)
        return format_spec + "d"

    def __init__(self, name, regex=REGEX + "+", format_spec="d", description=None):
        """
        Args:
            name (str): Name of the token

        Keyword Args:
            regex (str): Regex pattern for the string. Defaults to integer
                characters only
            format_spec (str): Python format string to use when formatting.
            description (str): Description message
        """
        super(IntToken, self).__init__(
            name, regex, format_spec, description=description or "Must be an integer"
        )

    def value_from_parsed_string(self, string):
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
    PADALIGN = constants.DEFAULT_PADALIGN_STR
    PADCHAR = constants.DEFAULT_PADCHAR_STR
    REGEX = constants.REGEX_STR

    @classmethod
    def get_format_spec_from_config(cls, config):
        """
        Args:
            config (dict): Dictionary of token configuration values

        Returns:
            str: Format spec for the token with the string "s" appended
        """
        format_spec = super(StringToken, cls).get_format_spec_from_config(config)
        return format_spec + "s"

    def __init__(self, name, regex=REGEX + "+", format_spec="s", description=None):
        """
        Args:
            name (str): Name of the token

        Keyword Args:
            regex (str): Regex pattern for the string. Defaults to alphabetical
                characters only
            format_spec (str): Python format string to use when formatting.
            description (str): Description message
        """
        super(StringToken, self).__init__(
            name, regex, format_spec, description=description or "Must be a string"
        )
