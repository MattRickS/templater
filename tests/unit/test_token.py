import pytest

from template_resolver import exceptions, token


class TestToken(object):
    @pytest.mark.parametrize(
        "config, expected",
        [
            ({}, ""),
            ({"format_spec": "<10"}, "<10"),
            ({"padmax": 3}, ""),
            ({"padmin": 3}, "0>3"),
            ({"padmin": 5, "padalign": "^", "padchar": "a"}, "a^5"),
        ],
    )
    def test_get_format_spec_from_config(self, config, expected):
        assert token.Token.get_format_spec_from_config(config) == expected

    def test_repr(self):
        t = token.Token("name", "[a-zA-Z]+", "")
        assert repr(t) == "Token('name', '[a-zA-Z]+', '', description='')"

    def test_str(self):
        t = token.Token("name", "[a-zA-Z]+", "")
        assert str(t) == "name"

    def test_name(self):
        t = token.Token("name", "", "")
        assert t.name == "name"

    def test_format(self):
        t = token.Token("name", "[a-zA-Z]+", "")
        assert t.format("abc") == "abc"

        with pytest.raises(exceptions.FormatError):
            t.format("123")

    def test_format_spec(self):
        t = token.Token("name", "[a-z]", "")
        assert t.format_spec == ""

    def test_parse(self):
        t = token.Token("name", "[a-zA-Z]+", "")
        assert t.parse("abc") == "abc"

        with pytest.raises(exceptions.ParseError):
            t.parse("ab2")

    def test_regex(self):
        t = token.Token("name", "[a-zA-Z]+", "")
        assert t.regex() == "[a-zA-Z]+"

    def test_value_from_parsed_string(self):
        t = token.Token("name", "[a-z]+", "s")
        assert t.value_from_parsed_string("abc") == "abc"


class TestIntToken(object):
    @pytest.mark.parametrize("config, expected", [({}, "d"), ({"padmin": 3}, "0=3d")])
    def test_get_format_spec_from_config(self, config, expected):
        assert token.IntToken.get_format_spec_from_config(config) == expected

    def test_format(self):
        t = token.IntToken("name")
        assert t.format(123) == "123"

        with pytest.raises(exceptions.FormatError):
            t.format("123")

        t = token.IntToken("name", format_spec="03")
        assert t.format(12) == "012"
        assert t.format(123) == "123"
        assert t.format(1234) == "1234"

    def test_format_spec(self):
        t = token.IntToken("name")
        assert t.format_spec == "d"

        # Whatever's passed in should remain unmodified
        t = token.IntToken("name", format_spec="03")
        assert t.format_spec == "03"

    def test_parse(self):
        t = token.IntToken("name")
        assert t.parse("123") == 123

        with pytest.raises(exceptions.ParseError):
            t.parse("12a")

    def test_value_from_parsed_string(self):
        t = token.IntToken("name")
        assert t.value_from_parsed_string("123") == 123

        with pytest.raises(exceptions.ParseError):
            t.value_from_parsed_string("abc")


class TestStringToken(object):
    @pytest.mark.parametrize("config, expected", [({}, "s"), ({"padmin": 3}, "s")])
    def test_get_format_spec_from_config(self, config, expected):
        assert token.StringToken.get_format_spec_from_config(config) == expected

    def test_format(self):
        t = token.StringToken("name")
        assert t.format("abc") == "abc"

        with pytest.raises(exceptions.FormatError):
            t.format("123")

        with pytest.raises(exceptions.FormatError):
            t.format(123)

        t = token.StringToken("name", format_spec="x>6")
        assert t.format("abcd") == "xxabcd"

    def test_format_spec(self):
        t = token.StringToken("name")
        assert t.format_spec == "s"

        # Whatever's passed in should remain unmodified
        t = token.StringToken("name", "[a-z]", format_spec="^10")
        assert t.format_spec == "^10"

    def test_parse(self):
        t = token.StringToken("name")
        assert t.parse("abc") == "abc"

    def test_value_from_parsed_string(self):
        t = token.StringToken("name")
        assert t.value_from_parsed_string("abc") == "abc"
