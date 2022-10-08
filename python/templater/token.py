import re
from typing import Any

from templater import constants, exceptions, util


class Token:
    PADALIGN = ">"
    PADCHAR = "0"
    REGEX = "."

    @classmethod
    def get_description_from_config(cls, config: dict) -> str:
        """
        Args:
            config: Dictionary of token configuration values

        Returns:
            Description message for the token
        """
        description = config.get("description")
        if not description:
            choices = config.get("choices")
            if choices:
                description = f"Must be one of: {choices}"
        return description

    @classmethod
    def get_format_spec_from_config(cls, config: dict) -> str:
        """
        Args:
            config: Dictionary of token configuration values

        Returns:
            Format spec for the token
        """
        format_spec = config.get("format_spec")
        if format_spec is None:
            padmin = config.get("padmin")
            padstrict = config.get("padstrict")
            if padmin is None or padstrict:
                format_spec = ""
            else:
                padalign = config.get("padalign", cls.PADALIGN)
                padchar = config.get("padchar", cls.PADCHAR)
                format_spec = "".join((padchar, padalign, str(padmin)))

        return format_spec

    @classmethod
    def get_regex_from_config(cls, config: dict) -> str:
        """
        Args:
            config: Dictionary of token configuration values

        Returns:
            Regex pattern for the token
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
            raise exceptions.ResolverError("Cannot use construction keywords with explicit regex")

        return regex

    def __init__(
        self, name: str, regex: str, format_spec: str, description: str = None, default: Any = None
    ):
        """
        Args:
            name: Name of the token
            regex: Regex pattern the token should capture
            format_spec: Python format string to use when formatting

        Keyword Args:
            description: Description for the token. Used to explain how the
                value should be formatted
            default: Default value to use for the token if no value is provided
        """
        self._name = name
        self._pattern = re.compile(f"^{regex}$")
        self._format_spec = format_spec
        self._description = description or ""
        self._default = default

    def __repr__(self) -> str:
        return (
            f"{self.__class__.__name__}({self.name!r}, {self.regex()!r}, {self.format_spec!r}, "
            f"description={self.description!r}, default={self.default})"
        )

    def __str__(self) -> str:
        return self._name

    @property
    def default(self) -> str:
        """
        Returns:
            Default value for the token
        """
        return self._default

    @property
    def description(self) -> str:
        """
        Returns:
            Description message to display for the token
        """
        return self._description

    @property
    def name(self) -> str:
        """
        Returns:
            Name of the token
        """
        return self._name

    @property
    def format_spec(self) -> str:
        """
        Returns:
            Python format spec for the token
        """
        return self._format_spec

    def format(self, value: Any) -> str:
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
            raise exceptions.FormatError(f"Value {value!r} does not match {self!r}")

        try:
            self.parse(string)
        except (ValueError, exceptions.ParseError):
            raise exceptions.FormatError(f"Value as string {string!r} does not match {self!r}")
        return string

    def parse(self, string: str) -> Any:
        """
        Raises:
            exceptions.ParseError: If the string doesn't match the token

        Args:
            string: String to parse the value from. Must match exactly.

        Returns:
            Parsed value
        """
        matched = self._pattern.match(string)
        if matched is None:
            raise exceptions.ParseError(f"String '{string}' does not match token {self!r}")

        value = self.value_from_parsed_string(string)
        return value

    def regex(self) -> str:
        """
        Returns:
            String pattern representing the regex
        """
        return self._pattern.pattern[1:-1]

    def value_from_parsed_string(self, string: str) -> Any:
        """
        Args:
            string: String to be converted to the token's value
        """
        return string


class IntToken(Token):
    PADALIGN = constants.DEFAULT_PADALIGN_INT
    PADCHAR = constants.DEFAULT_PADCHAR_INT
    REGEX = constants.REGEX_INT

    @classmethod
    def get_description_from_config(cls, config: dict) -> str:
        """
        Args:
            config: Dictionary of token configuration values

        Returns:
            Description message for the token
        """
        description = super(IntToken, cls).get_description_from_config(config)
        if description is None:
            padmin = config.get("padmin")
            padmax = config.get("padmax")
            if padmin is not None and padmin == padmax:
                description = f"Must be a {padmin}-digit integer"
            elif padmin is not None:
                description = f"Must be a minimum {padmin}-digit integer"
            elif padmax is not None:
                description = f"Must be a maximum {padmax}-digit integer"
            else:
                description = "Must be an integer"
        return description

    @classmethod
    def get_format_spec_from_config(cls, config: dict) -> str:
        """
        Args:
            config: Dictionary of token configuration values

        Returns:
            Format spec for the token with the integer "d" appended
        """
        format_spec = super(IntToken, cls).get_format_spec_from_config(config)
        return format_spec + "d"

    def __init__(
        self,
        name: str,
        regex: str = REGEX + "+",
        format_spec: str = "d",
        description: str = None,
        default: str = None,
    ):
        """
        Args:
            name: Name of the token

        Keyword Args:
            regex: Regex pattern for the string. Defaults to integer
                characters only
            format_spec: Python format string to use when formatting.
            description: Description message
            default: Default value to use for the token if no value is provided
        """
        super(IntToken, self).__init__(
            name, regex, format_spec, description=description, default=default
        )

    def value_from_parsed_string(self, string: str) -> int:
        """
        Args:
            string: String value

        Returns:
            Integer value
        """
        try:
            return int(string)
        except ValueError:
            raise exceptions.ParseError(
                f"String '{string}' does not match int token '{self._name}'"
            )


class StringToken(Token):
    PADALIGN = constants.DEFAULT_PADALIGN_STR
    PADCHAR = constants.DEFAULT_PADCHAR_STR
    REGEX = constants.REGEX_STR

    @classmethod
    def get_description_from_config(cls, config: dict) -> str:
        """
        Args:
            config: Dictionary of token configuration values

        Returns:
            Description message for the token
        """
        description = super(StringToken, cls).get_description_from_config(config)
        if description is None:
            padmin = config.get("padmin")
            padmax = config.get("padmax")
            case = config.get("case")
            case = f"{case} case " if case else ""

            if padmin is not None and padmin == padmax:
                description = f"Must be a {padmin}-character {case}string"
            elif padmin is not None:
                description = f"Must be a minimum {padmin}-character {case}string"
            elif padmax is not None:
                description = f"Must be a maximum {padmax}-character {case}string"
            else:
                description = f"Must be a {case}string"
        return description

    @classmethod
    def get_format_spec_from_config(cls, config: dict) -> str:
        """
        Args:
            config: Dictionary of token configuration values

        Returns:
            Format spec for the token with the string "s" appended
        """
        # Enable strict padding by default unless set
        config.setdefault("padstrict", True)
        format_spec = super(StringToken, cls).get_format_spec_from_config(config)
        return format_spec + "s"

    @classmethod
    def get_regex_from_config(cls, config: dict) -> str:
        """
        Args:
            config: Dictionary of token configuration values

        Returns:
            Regex pattern for the token
        """
        case = config.get("case")
        regex = config.get("regex")
        if regex is None and case:
            regex = util.get_case_regex(case)
            padmin = config.get("padmin")
            padmax = config.get("padmax")
            # Camel cases add a fixed starting character, modify padding accordingly
            if case in (constants.Case.LowerCamel, constants.Case.UpperCamel):
                padmin = (padmin - 1) if padmin else None
                padmax = (padmax - 1) if padmax else None
            regex += util.get_regex_padding(padmin=padmin, padmax=padmax)
        elif case is not None:
            raise exceptions.ResolverError("Cannot use construction keywords with explicit regex")
        else:
            regex = super(StringToken, cls).get_regex_from_config(config)
        return regex

    def __init__(
        self,
        name: str,
        regex: str = REGEX + "+",
        format_spec: str = "s",
        description: str = None,
        default: str = None,
    ):
        """
        Args:
            name: Name of the token

        Keyword Args:
            regex: Regex pattern for the string. Defaults to alphabetical
                characters only
            format_spec: Python format string to use when formatting.
            description: Description message
            default: Default value to use for the token if no value is provided
        """
        super(StringToken, self).__init__(
            name, regex, format_spec, description=description, default=default
        )
