import re
import six

from template_resolver import exceptions, token


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
        return self._name

    @property
    def name(self):
        """
        Returns:
            str: Name of the template
        """
        return self._name

    def extract(self, string, index=0):
        """
        Attempts to extract the template from a section of the string. Does not
        have to match the full remainder of the string.

        Raises:
            exceptions.ParseError: If the string doesn't match the template
            exceptions.TokenConflictError: If a repeated token matches
                conflicting values

        Args:
            string (str): String to extract the template from

        Keyword Args:
            index (int): Index to start extracting from, defaults to the start
                of the string

        Returns:
            tuple[dict, int]: Tuple containing the dictionary of parsed fields
                and the index the match finished on
        """
        fields = {}
        for segment in self._segments:
            if isinstance(segment, Template):
                template_fields, index = segment.extract(string, index=index)
                overlap = set(template_fields).intersection(fields)
                for field in overlap:
                    if fields[field] != template_fields[field]:
                        raise exceptions.TokenConflictError(
                            field, [fields[field], template_fields[field]]
                        )
                fields.update(template_fields)
            elif isinstance(segment, token.Token):
                value, index = segment.extract(string, index=index)
                if segment.name in fields and fields[segment.name] != value:
                    raise exceptions.TokenConflictError(
                        segment.name, [fields[segment.name], value]
                    )
                fields[segment.name] = value
            elif isinstance(segment, six.string_types):
                end = index + len(segment)
                if string[index:end] != segment:
                    raise exceptions.ParseError(
                        "Segment does not match: {!r} != {!r}".format(
                            segment, string[index:end]
                        )
                    )
                index = end
            else:
                raise TypeError("Unknown segment: {}".format(segment))
        return fields, index

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

    def format(self, fields):
        """
        Raises:
            exceptions.FormatError: If the fields don't match the template

        Args:
            fields (dict): Dictionary of fields to format the template with,
                must match tokens

        Returns:
            str: Formatted template string
        """
        segments = []
        for segment in self._segments:
            if isinstance(segment, six.string_types):
                string_segment = segment
            elif isinstance(segment, Template):
                string_segment = segment.format(fields)
            elif isinstance(segment, token.Token):
                if segment.name not in fields:
                    raise exceptions.MissingTokenError(segment.name)
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
            exceptions.TokenConflictError: If a repeated token matches
                conflicting values

        Args:
            string (str): String to parse the template tokens from

        Returns:
            dict: Dictionary of fields extracted from the tokens
        """
        fields, end = self.extract(string)
        if end != len(string):
            raise exceptions.ParseError(
                "Incomplete match, remaining string: {!r}".format(string[end:])
            )
        return fields

    def pattern(self):
        """
        Raises:
            TypeError: If any segments are an unknown type

        Returns:
            str: Standard format string representing the template, eg,
                word_{tokenA}_{tokenB}
        """
        segments = []
        for segment in self._segments:
            if isinstance(segment, six.string_types):
                string_segment = segment
            elif isinstance(segment, token.Token):
                string_segment = "{{{}}}".format(segment.name)
            elif isinstance(segment, Template):
                string_segment = segment.pattern()
            else:
                raise TypeError("Unknown segment type: {}".format(segment))
            segments.append(string_segment)
        return "".join(segments)

    def regex(self):
        """
        Returns:
            str: Regex string for matching the entire template
        """
        return "".join(
            [
                re.escape(segment)
                if isinstance(segment, six.string_types)
                else segment.regex()
                for segment in self._segments
            ]
        )

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
