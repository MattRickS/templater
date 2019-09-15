import six

from template_resolver import exceptions, token


class Template(object):
    def __init__(self, name, segments):
        self._name = name
        self._segments = segments

    def __repr__(self):
        return "{s.__class__.__name__}({s._name!r}, {s._segments})".format(s=self)

    def __str__(self):
        return self._name

    @property
    def name(self):
        return self._name

    def extract(self, string, index=0):
        fields = {}
        for segment in self._segments:
            if isinstance(segment, Template):
                template_fields, index = segment.extract(string, index=index)
                overlap = set(template_fields).intersection(fields)
                for field in overlap:
                    if fields[field] != template_fields[field]:
                        raise exceptions.ParseError(
                            "Mismatched values found for {!r}: {!r} != {!r}".format(
                                segment._name, fields[field], template_fields[field]
                            )
                        )
                fields.update(template_fields)
            elif isinstance(segment, token.Token):
                value, index = segment.extract(string, index=index)
                if segment.name in fields and fields[segment.name] != value:
                    raise exceptions.ParseError(
                        "Mismatched values found for {!r}: {!r} != {!r}".format(
                            segment.name, fields[segment.name], value
                        )
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
        strings = []
        for segment in self._segments:
            if isinstance(segment, six.string_types):
                strings.append(segment)
            elif isinstance(segment, Template) and not local_only:
                strings.extend(segment.fixed_strings(local_only=local_only))

        return strings

    def format(self, fields):
        # A template can be provided in full
        if self._name in fields:
            field = fields[self._name]
            try:
                self.parse(field)
            except exceptions.ParseError:
                raise exceptions.FormatError(
                    "Value {!r} does not match template {!r}".format(field, self._name)
                )
            return field

        segments = []
        for segment in self._segments:
            if isinstance(segment, six.string_types):
                string_segment = segment
            elif isinstance(segment, Template):
                string_segment = segment.format(fields)
            elif isinstance(segment, token.Token):
                string_segment = segment.format(fields[segment.name])
            else:
                raise TypeError("Unknown segment: {}".format(segment))
            segments.append(string_segment)
        return "".join(segments)

    def parse(self, string):
        fields, end = self.extract(string)
        if end != len(string):
            raise exceptions.ParseError(
                "Incomplete match, remaining string: {!r}".format(string[end:])
            )
        return fields

    def pattern(self):
        segments = []
        for segment in self._segments:
            if isinstance(segment, six.string_types):
                string_segment = segment
            elif isinstance(segment, token.Token):
                string_segment = "{{{}}}".format(segment.name)
            elif isinstance(segment, Template):
                string_segment = segment.pattern()
            else:
                raise ValueError("Unknown segment")
            segments.append(string_segment)
        return "".join(segments)

    def regex(self):
        return "".join(
            [
                segment if isinstance(segment, six.string_types) else segment.regex()
                for segment in self._segments
            ]
        )

    def segments(self, local_only=False):
        segments = []
        for segment in self._segments:
            if isinstance(segment, Template) and not local_only:
                segments.extend(segment.segments(local_only=local_only))
            else:
                segments.append(segment)
        return segments

    def templates(self, local_only=False):
        templates = []
        for segment in self._segments:
            if isinstance(segment, Template):
                templates.append(segment)
                if not local_only:
                    templates.extend(segment.templates(local_only=local_only))

        return templates

    def tokens(self, local_only=False):
        return [
            segment
            for segment in self.segments(local_only=local_only)
            if isinstance(segment, token.Token)
        ]
