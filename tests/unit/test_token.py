import pytest

from template_resolver import exceptions, token


class TestToken(object):
    def test_repr(self):
        t = token.Token("name", "[a-zA-Z]+")
        assert repr(t) == "Token('name', '[a-zA-Z]+')"

    def test_str(self):
        t = token.Token("name", "[a-zA-Z]+")
        assert str(t) == "name"

    def test_name(self):
        t = token.Token("name", "")
        assert t.name == "name"

    def test_format(self):
        t = token.Token("name", "[a-zA-Z]+")
        assert t.format("abc") == "abc"

        with pytest.raises(exceptions.FormatError):
            t.format("123")

    def test_format_string(self):
        t = token.Token("name", "[a-z]", format_string="")
        assert t.format_string == ""

    def test_parse(self):
        t = token.Token("name", "[a-zA-Z]+")
        assert t.parse("abc") == "abc"

        with pytest.raises(exceptions.ParseError):
            t.parse("ab2")

    def test_regex(self):
        t = token.Token("name", "[a-zA-Z]+")
        assert t.regex() == "[a-zA-Z]+"


class TestIntToken(object):
    def test_format(self):
        t = token.IntToken("name")
        assert t.format(123) == "123"

        with pytest.raises(exceptions.FormatError):
            t.format("123")

        t = token.IntToken("name", format_string="03")
        assert t.format(12) == "012"
        assert t.format(123) == "123"
        assert t.format(1234) == "1234"

    @pytest.mark.parametrize("format_string, expected", [("", "d"), ("03", "03d")])
    def test_format_string(self, format_string, expected):
        t = token.IntToken("name", "[a-z]", format_string=format_string)
        assert t.format_string == expected

    def test_parse(self):
        t = token.IntToken("name")
        assert t.parse("123") == 123

        with pytest.raises(exceptions.ParseError):
            t.parse("12a")


class TestStringToken(object):
    def test_format(self):
        t = token.StringToken("name")
        assert t.format("abc") == "abc"

        with pytest.raises(exceptions.FormatError):
            t.format("123")

        with pytest.raises(exceptions.FormatError):
            t.format(123)

        t = token.StringToken("name", format_string="x>6")
        assert t.format("abcd") == "xxabcd"

    @pytest.mark.parametrize("format_string, expected", [("", "s"), ("<10", "<10s")])
    def test_format_string(self, format_string, expected):
        t = token.StringToken("name", "[a-z]", format_string=format_string)
        assert t.format_string == expected

    def test_parse(self):
        t = token.StringToken("name")
        assert t.parse("abc") == "abc"
