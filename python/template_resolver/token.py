import re

from template_resolver import exceptions


class Token(object):
    def __init__(self, name, regex):
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
        return self._name

    def extract(self, string, index=0):
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
        try:
            self.parse(value)
        except exceptions.ParseError:
            raise exceptions.FormatError(
                "Value {!r} does not match {!r}".format(value, self)
            )
        return value

    def parse(self, string):
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
        return self._pattern.pattern


class IntToken(Token):
    def __init__(self, name, regex="[0-9]+"):
        super(IntToken, self).__init__(name, regex)

    def extract(self, string, index=0):
        value, end = super(IntToken, self).extract(string, index=index)
        return int(value), end

    def format(self, value):
        return super(IntToken, self).format(str(value))

    def parse(self, string):
        value = super(IntToken, self).parse(string)
        return int(value)


class StringToken(Token):
    def __init__(self, name, regex="[a-zA-Z]+"):
        super(StringToken, self).__init__(name, regex)

    def format(self, value):
        return super(StringToken, self).format(str(value))
