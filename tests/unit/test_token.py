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

    @pytest.mark.parametrize(
        "regex, string, index, expected_value, expected_end",
        [("[a-zA-Z]+", "abc", 0, "abc", 3), ("[a-zA-Z]+", "abc123", 0, "abc", 3)],
    )
    def test_extract(self, regex, string, index, expected_value, expected_end):
        t = token.Token("name", regex)
        value, end = t.extract(string, index=index)
        assert value == expected_value
        assert end == expected_end

    def test_format(self):
        t = token.Token("name", "[a-zA-Z]+")
        assert t.format("abc") == "abc"

        with pytest.raises(exceptions.FormatError):
            t.format("123")

    def test_parse(self):
        t = token.Token("name", "[a-zA-Z]+")
        assert t.parse("abc") == "abc"

        with pytest.raises(exceptions.ParseError):
            t.parse("ab2")

    def test_regex(self):
        t = token.Token("name", "[a-zA-Z]+")
        assert t.regex() == "[a-zA-Z]+"


class TestIntToken(object):
    @pytest.mark.parametrize(
        "string, index, expected_value, expected_end",
        [("123", 0, 123, 3), ("123abc", 0, 123, 3)],
    )
    def test_extract(self, string, index, expected_value, expected_end):
        t = token.IntToken("name")
        value, end = t.extract(string, index=index)
        assert value == expected_value
        assert end == expected_end

    def test_format(self):
        t = token.IntToken("name")
        assert t.format(123) == "123"
        assert t.format("123") == "123"

        with pytest.raises(exceptions.FormatError):
            t.format("12a")

    def test_parse(self):
        t = token.IntToken("name")
        assert t.parse("123") == 123

        with pytest.raises(exceptions.ParseError):
            t.parse("12a")


class TestStringToken(object):
    def test_format(self):
        t = token.AlphaToken("name")
        assert t.format("abc") == "abc"

        with pytest.raises(exceptions.FormatError):
            t.format("123")

        with pytest.raises(exceptions.FormatError):
            t.format(123)

    def test_parse(self):
        t = token.AlphaToken("name")
        assert t.parse("abc") == "abc"
