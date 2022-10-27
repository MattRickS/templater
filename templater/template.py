from __future__ import annotations
import re
from typing import Any, Dict, List, Tuple, Union

from templater import exceptions, token


class Template:
    def __init__(self, name: str, segments: List[Union[str, token.Token, Template]]):
        """
        Args:
            name: Name of the template
            segments: List of path segments
        """
        self._name = name
        self._segments = segments

    def __repr__(self):
        return f"{self.__class__.__name__}({self._name!r}, {self._segments})"

    def __str__(self):
        return ":".join((self._name, self.pattern()))

    def __eq__(self, template: Template) -> bool:
        return self.name == template.name and self._segments == template._segments

    @property
    def name(self) -> str:
        """
        Returns:
            Name of the template
        """
        return self._name

    def extract(self, string: str) -> Tuple[Dict[str, Any], int]:
        """
        Attempts to extract the template from a section of the string. Does not
        have to match the full string.

        Raises:
            exceptions.ParseError: If the string doesn't match the template

        Args:
            string: String to extract the template from

        Returns:
            Tuple containing the dictionary of parsed fields and the index the
                match finished on
        """
        regex = self.regex()
        fields, end = self._parse(regex, string)
        return fields, end

    def fixed_strings(self, local_only: bool = False) -> List[str]:
        """
        Keyword Args:
            local_only: Whether or not to include fixed string segments
                from child templates

        Returns:
            List of string segments
        """
        return [
            segment for segment in self.segments(local_only=local_only) if isinstance(segment, str)
        ]

    def format(
        self, fields: Dict[str, Any], unformatted: Dict[str, str] = None, use_defaults: bool = True
    ) -> str:
        """
        Raises:
            exceptions.FormatError: If the fields don't match the template

        Args:
            fields: Dictionary of fields to format the template with, must match
                tokens

        Keyword Args:
            unformatted: Dictionary of token names mapping to values. Fields in
                unformatted skip formatting checks and use the given string
                instead. This is intended to allow custom wildcard formatting
                for search functions.
            use_defaults: Whether or not to use token's default values for
                missing fields.

        Returns:
            Formatted template string
        """
        unformatted = unformatted or {}
        segments = []
        for segment in self._segments:
            if isinstance(segment, str):
                string_segment = segment
            elif isinstance(segment, Template):
                string_segment = segment.format(fields)
            elif isinstance(segment, token.Token):
                if segment.name in unformatted:
                    string_segment = unformatted[segment.name]
                elif segment.name not in fields:
                    if use_defaults and segment.default is not None:
                        string_segment = str(segment.default)
                    else:
                        raise exceptions.MissingTokenError(segment.name)
                else:
                    string_segment = segment.format(fields[segment.name])
            else:
                raise TypeError(f"Unknown segment type: {segment}")
            segments.append(string_segment)
        return "".join(segments)

    def parse(self, string: str) -> Dict[str, Any]:
        """
        Raises:
            exceptions.ParseError: If the string doesn't match the template
                exactly

        Args:
            string: String to parse the template tokens from

        Returns:
            Dictionary of fields extracted from the tokens
        """
        regex = f"^{self.regex()}$"
        fields, _ = self._parse(regex, string)
        return fields

    def parse_debug(self, string: str) -> Dict[str, Any]:
        """
        Parses the string, but raises more descriptive errors at the cost of
        extra calculation

        Raises:
            exceptions.DebugParseError: If the string doesn't match the template
                exactly

        Args:
            string: String to parse the template tokens from

        Returns:
            Dictionary of fields extracted from the tokens
        """
        segments = self.segments()
        regexes = [
            f"({segment if isinstance(segment, str) else segment.regex()})" for segment in segments
        ]
        num_segments = len(segments)

        for segment_index in range(num_segments, 0, -1):
            pattern = "".join(regexes[:segment_index])
            match = re.match(pattern, string)
            if match is None:
                continue

            fields = {}
            for i, (segment, value) in enumerate(zip(segments, match.groups())):
                if isinstance(segment, str):
                    continue

                # group 0 is the entire string, add one to find the actual group
                char_index, _ = match.span(i + 1)

                try:
                    value = segment.value_from_parsed_string(value)
                except exceptions.ParseError as e:
                    raise exceptions.DebugParseError(str(e), char_index, i, fields)

                if segment.name in fields and fields[segment.name] != value:
                    # Remove the invalid field before raising
                    previous_value = fields.pop(segment.name)
                    raise exceptions.MismatchTokenError(
                        f"Mismatched values for token {{{segment.name}}}: {previous_value} != {value}",
                        char_index,
                        i,
                        fields,
                    )

                fields[segment.name] = value

            # Matched on the first pattern, ie, the whole template
            if segment_index == num_segments:
                if match.group(0) != string:
                    _, end = match.span(0)
                    raise exceptions.ExcessStringError(
                        "Template matches string with remainder",
                        end,
                        num_segments,
                        fields,
                    )
                return fields

            segment = segments[segment_index]
            char_index = match.end()
            if isinstance(segment, str):
                for char_index, (a, b) in enumerate(
                    zip(segment, string[char_index:]), start=char_index
                ):
                    if a != b:
                        break

            segname = f"'{segment}'" if isinstance(segment, str) else f"{{{segment.name}}}"
            raise exceptions.DebugParseError(
                f"Match fails at segment ({segment_index}) {segname}",
                char_index,
                segment_index,
                fields,
            )

        raise exceptions.DebugParseError("String does not match at all", 0, 0, {})

    def pattern(self, formatters: bool = False) -> str:
        """
        Raises:
            TypeError: If any segments are an unknown type

        Keyword Args:
            formatters: Whether or not to include token formatters in the
                pattern

        Returns:
            Standard format string representing the template, eg,
                word_{tokenA}_{tokenB}
        """
        segments = []
        for segment in self._segments:
            if isinstance(segment, str):
                string_segment = segment
            elif isinstance(segment, token.Token):
                if formatters:
                    string_segment = f"{{{segment.name}:{segment.format_spec}}}"
                else:
                    string_segment = f"{{{segment.name}}}"
            elif isinstance(segment, Template):
                string_segment = segment.pattern(formatters=formatters)
            else:
                raise TypeError(f"Unknown segment type: {segment}")
            segments.append(string_segment)
        return "".join(segments)

    def regex(self, backreferences: List[str] = None) -> str:
        """
        Returns:
            Regex string for matching the entire template
        """
        backreferences = backreferences or []
        segments = []
        for segment in self._segments:
            if isinstance(segment, str):
                pattern = re.escape(segment)
            elif isinstance(segment, Template):
                pattern = segment.regex(backreferences=backreferences)
            elif isinstance(segment, token.Token):
                if segment.name in backreferences:
                    pattern = f"(?P={segment.name})"
                else:
                    pattern = f"(?P<{segment.name}>{segment.regex()})"
                    backreferences.append(segment.name)
            else:
                raise TypeError(f"Unknown segment type: {segment}")
            segments.append(pattern)

        return "".join(segments)

    def segments(self, local_only: bool = False) -> List[Union[str, token.Token, Template]]:
        """
        Keyword Args:
            local_only: Whether or not to expand any child templates into
                their contained segments

        Returns:
            List of segments in the template
        """
        segments = []
        for segment in self._segments:
            if isinstance(segment, Template) and not local_only:
                segments.extend(segment.segments(local_only=local_only))
            else:
                segments.append(segment)
        return segments

    def templates(self, local_only: bool = False) -> List[Template]:
        """
        Keyword Args:
            local_only: Whether or not to include all descendant templates

        Returns:
            List of all template segments
        """
        templates = []
        for segment in self._segments:
            if isinstance(segment, Template):
                templates.append(segment)
                if not local_only:
                    templates.extend(segment.templates(local_only=local_only))

        return templates

    def tokens(self, local_only: bool = False) -> List[token.Token]:
        """
        Keyword Args:
            local_only: Whether or not to expand any child templates into
                their contained tokens

        Returns:
            List of token segments
        """
        return [
            segment
            for segment in self.segments(local_only=local_only)
            if isinstance(segment, token.Token)
        ]

    def _parse(self, regex: str, string: str) -> Tuple[Dict[str, Any], int]:
        match = re.match(regex, string)
        if not match:
            raise exceptions.ParseError(f"String '{string}' doesn't match template '{self}'")

        string_fields = match.groupdict()
        # Convert the string value to the token type
        fields = {
            token_obj.name: token_obj.value_from_parsed_string(string_fields[token_obj.name])
            for token_obj in self.tokens()
        }
        return fields, match.end()
