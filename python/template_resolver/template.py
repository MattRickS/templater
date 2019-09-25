import re
import six

from template_resolver import constants, exceptions, token


class Template(object):
    def __init__(self, name, segments):
        """
        Args:
            name (str): Name of the template
            segments (list[str|token.Token|Template]): List of path segments
        """
        self._name = name
        self._segments = segments

    def __repr__(self):
        return "{s.__class__.__name__}({s._name!r}, {s._segments})".format(s=self)

    def __str__(self):
        return ":".join((self._name, self.pattern()))

    @property
    def name(self):
        """
        Returns:
            str: Name of the template
        """
        return self._name

    def extract(self, string):
        """
        Attempts to extract the template from a section of the string. Does not
        have to match the full string.

        Raises:
            exceptions.ParseError: If the string doesn't match the template

        Args:
            string (str): String to extract the template from

        Returns:
            tuple[dict, int]: Tuple containing the dictionary of parsed fields
                and the index the match finished on
        """
        regex = self.regex()
        fields, end = self._parse(regex, string)
        return fields, end

    def fixed_strings(self, local_only=False):
        """
        Keyword Args:
            local_only (bool): Whether or not to include fixed string segments
                from child templates

        Returns:
            list[str]: List of string segments
        """
        return [
            segment
            for segment in self.segments(local_only=local_only)
            if isinstance(segment, six.string_types)
        ]

    def format(self, fields, wildcards=None):
        """
        Raises:
            exceptions.FormatError: If the fields don't match the template

        Args:
            fields (dict): Dictionary of fields to format the template with,
                must match tokens

        Keyword Args:
            wildcards (list[str]): List of field names to skip formatting and
                use a wildcard symbol for

        Returns:
            str: Formatted template string
        """
        wildcards = wildcards or []
        segments = []
        for segment in self._segments:
            if isinstance(segment, six.string_types):
                string_segment = segment
            elif isinstance(segment, Template):
                string_segment = segment.format(fields)
            elif isinstance(segment, token.Token):
                if segment.name in wildcards:
                    string_segment = constants.SYMBOL_WILDCARD
                elif segment.name not in fields:
                    raise exceptions.MissingTokenError(segment.name)
                else:
                    string_segment = segment.format(fields[segment.name])
            else:
                raise TypeError("Unknown segment type: {}".format(segment))
            segments.append(string_segment)
        return "".join(segments)

    def parse(self, string):
        """
        Raises:
            exceptions.ParseError: If the string doesn't match the template
                exactly

        Args:
            string (str): String to parse the template tokens from

        Returns:
            dict: Dictionary of fields extracted from the tokens
        """
        regex = "^{}$".format(self.regex())
        fields, _ = self._parse(regex, string)
        return fields

    def pattern(self, formatters=False):
        """
        Raises:
            TypeError: If any segments are an unknown type

        Keyword Args:
            formatters (bool): Whether or not to include token formatters in the
                pattern

        Returns:
            str: Standard format string representing the template, eg,
                word_{tokenA}_{tokenB}
        """
        segments = []
        for segment in self._segments:
            if isinstance(segment, six.string_types):
                string_segment = segment
            elif isinstance(segment, token.Token):
                if formatters:
                    string_segment = "{{{}:{}}}".format(
                        segment.name, segment.format_spec
                    )
                else:
                    string_segment = "{{{}}}".format(segment.name)
            elif isinstance(segment, Template):
                string_segment = segment.pattern(formatters=formatters)
            else:
                raise TypeError("Unknown segment type: {}".format(segment))
            segments.append(string_segment)
        return "".join(segments)

    def regex(self, backreferences=None):
        """
        Returns:
            str: Regex string for matching the entire template
        """
        backreferences = backreferences or []
        segments = []
        for segment in self._segments:
            if isinstance(segment, six.string_types):
                pattern = re.escape(segment)
            elif isinstance(segment, Template):
                pattern = segment.regex(backreferences=backreferences)
            elif isinstance(segment, token.Token):
                if segment.name in backreferences:
                    pattern = "(?P={})".format(segment.name)
                else:
                    pattern = "(?P<{}>{})".format(segment.name, segment.regex())
                    backreferences.append(segment.name)
            else:
                raise TypeError("Unknown segment type: {}".format(segment))
            segments.append(pattern)

        return "".join(segments)

    def segments(self, local_only=False):
        """
        Keyword Args:
            local_only (bool): Whether or not to expand any child templates into
                their contained segments

        Returns:
            list[str|token.Token|Template]: List of segments in the template
        """
        segments = []
        for segment in self._segments:
            if isinstance(segment, Template) and not local_only:
                segments.extend(segment.segments(local_only=local_only))
            else:
                segments.append(segment)
        return segments

    def templates(self, local_only=False):
        """
        Keyword Args:
            local_only (bool): Whether or not to include all descendant
                templates

        Returns:
            list[Template]: List of all template segments
        """
        templates = []
        for segment in self._segments:
            if isinstance(segment, Template):
                templates.append(segment)
                if not local_only:
                    templates.extend(segment.templates(local_only=local_only))

        return templates

    def tokens(self, local_only=False):
        """
        Keyword Args:
            local_only (bool): Whether or not to expand any child templates into
                their contained tokens

        Returns:
            list[token.Token]: List of token segments
        """
        return [
            segment
            for segment in self.segments(local_only=local_only)
            if isinstance(segment, token.Token)
        ]

    def _parse(self, regex, string):
        match = re.match(regex, string)
        if not match:
            raise exceptions.ParseError(
                "String {} doesn't match template {}".format(string, self)
            )

        string_fields = match.groupdict()
        # Convert the string value to the token type
        fields = {
            token_obj.name: token_obj.value_from_parsed_string(
                string_fields[token_obj.name]
            )
            for token_obj in self.tokens()
        }
        return fields, match.end()

    def debug_parse(self, string):
        segments = self.segments()
        names = [
            None if isinstance(segment, six.string_types) else segment.name
            for segment in segments
        ]
        patterns = [
            segment if isinstance(segment, six.string_types) else segment.regex()
            for segment in segments
        ]
        patterns.append("$")
        regex_segments = [
            "(?=({}))?".format("".join(patterns[: i + 1])) for i in range(len(patterns))
        ]
        regex_segments.append(".")
        regex = "".join(regex_segments)
        match = re.match(regex, string)
        fields = {}
        if match is None:
            raise DebugParseError("No segments match", -1, None, fields)
        else:
            groups = match.groups()
            print(groups)
            for index, (name, value) in enumerate(zip(names, groups)):
                if value is None:
                    failed_segment = segments[index]
                    raise DebugParseError(
                        "Segment ({}) '{}' doesn't match".format(index, failed_segment),
                        index,
                        failed_segment,
                        fields,
                    )
                # Values are full string matches. Extract the difference
                # from the previous value
                if index > 0:
                    value = value[len(groups[index - 1]) :]

                if name in fields and fields[name] != value:
                    raise DebugParseError(
                        "Duplicate tokens don't match for segment ({}) '{}': "
                        "'{}' != '{}'".format(
                            index, name, value, fields[name]
                        ),
                        index,
                        value,
                        fields,
                    )
                if name is not None:
                    fields[name] = value

        return fields


class DebugParseError(exceptions.ParseError):
    def __init__(self, message, index, segment, fields):
        super(DebugParseError, self).__init__(message)
        self.index = index
        self.segment = segment
        self.fields = fields


if __name__ == "__main__":
    t = Template(
        "name",
        [
            token.StringToken("name"),
            "_",
            token.StringToken("other"),
            "_",
            token.IntToken("num"),
            "_",
            token.StringToken("name"),
        ],
    )
    for text in (
        "1",
        "abc",
        "abc_",
        "abc_def1_1",
        "abc_def_ghi",
        "abc_def_1",
        "abc_def_1_",
        "abc_def_1_ghi",
        "abc_def_1_abc",
    ):
        try:
            f = t.debug_parse(text)
        except DebugParseError as e:
            print(e)
        else:
            print("passed:", text, f)

    # Fails - the fields are {"name": "abcdef"} because the token can capture
    # the entire string, so the first regex capture stores the wrong field value
    t = Template(
        "name",
        [
            token.StringToken("name"),
            "def",
        ],
    )
    for text in (
        "abc",
        "abcdef",
    ):
        try:
            f = t.debug_parse(text)
        except DebugParseError as e:
            print(e)
        else:
            print("passed:", text, f)
