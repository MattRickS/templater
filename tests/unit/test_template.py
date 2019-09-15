import pytest

from template_resolver import exceptions, template, token


class TestTemplate(object):
    def test_repr(self):
        t = template.Template("name", ["abc", "def"])
        assert repr(t) == "Template('name', ['abc', 'def'])"

    def test_str(self):
        t = template.Template("name", ["abc", "def"])
        assert str(t) == "name"

    def test_name(self):
        t = template.Template("name", ["abc", "def"])
        assert t.name == "name"

    def test_segments(self):
        t = template.Template("name", ["abc", "def"])
        assert t.segments() == ["abc", "def"]

        # Should return a copy, original should be unmodified
        t.segments()[0] = "ghi"
        assert t.segments() == ["abc", "def"]

    @pytest.mark.parametrize(
        "segments, local_only, expected",
        [
            (["abc", token.StringToken("one"), "def"], False, ["abc", "def"]),
            (
                ["abc", template.Template("temp", ["ghi"]), "def"],
                False,
                ["abc", "ghi", "def"],
            ),
            (["abc", template.Template("temp", ["ghi"]), "def"], True, ["abc", "def"]),
        ],
    )
    def test_fixed_strings(self, segments, local_only, expected):
        t = template.Template("name", segments)
        assert t.fixed_strings(local_only=local_only) == expected

    @pytest.mark.parametrize(
        "segments, fields, expected",
        [
            (["abc", token.IntToken("int"), "def"], {"int": 1}, "abc1def"),
            (
                [token.StringToken("str"), "_", token.IntToken("int")],
                {"int": 30, "str": "word"},
                "word_30",
            ),
            # Duplicates of a token should use the same value
            ([token.IntToken("int"), "_", token.IntToken("int")], {"int": 1}, "1_1"),
        ],
    )
    def test_format(self, segments, fields, expected):
        t = template.Template("name", segments)
        assert t.format(fields) == expected

    @pytest.mark.parametrize(
        "segments, string, expected",
        [
            (["abc", token.IntToken("int"), "def"], "abc1def", {"int": 1}),
            (
                [token.StringToken("str"), "_", token.IntToken("int")],
                "word_30",
                {"int": 30, "str": "word"},
            ),
            # Duplicates of a token must parse the same value
            ([token.IntToken("int"), "_", token.IntToken("int")], "1_1", {"int": 1}),
        ],
    )
    def test_parse(self, segments, string, expected):
        t = template.Template("name", segments)
        assert t.parse(string) == expected

    def test_parse_invalid_string_error(self):
        t = template.Template("name", [token.StringToken("str"), token.IntToken("int")])

        # Inverted order
        with pytest.raises(exceptions.ParseError):
            t.parse("10abc")

        # Intermediate value "_"
        with pytest.raises(exceptions.ParseError):
            t.parse("abc_10")

    def test_parse_token_conflict_error(self):
        t = template.Template(
            "name",
            [token.StringToken("str"), token.IntToken("int"), token.StringToken("str")],
        )

        # Both tokens called "str" must have the same value
        with pytest.raises(exceptions.TokenConflictError) as exc_info:
            t.parse("abc1def")

        assert exc_info.value.token_name == "str"
        assert exc_info.value.values == ["abc", "def"]

    def test_pattern(self):
        t = template.Template(
            "name", ["abc_", token.IntToken("int"), ".def.", token.StringToken("str")]
        )
        assert t.pattern() == "abc_{int}.def.{str}"

    def test_regex(self):
        t = template.Template(
            "name", ["abc_", token.IntToken("int"), ".def.", token.StringToken("str")]
        )
        assert t.regex() == r"abc_[0-9]+\.def\.[a-zA-Z]+"

    def test_templates(self):
        # No template segments should return an empty list
        t1 = template.Template("t1", ["abc", token.StringToken("str")])
        assert t1.templates(local_only=True) == []
        assert t1.templates(local_only=False) == []

        # Template is a first level member of segments and should be in both
        t2 = template.Template("t2", ["def", t1])
        assert t2.templates(local_only=True) == [t1]
        assert t2.templates(local_only=False) == [t1]

        # t1 is a "grandchild" of t3 and should be omitted from local
        t3 = template.Template("t3", [t2, "ghi"])
        assert t3.templates(local_only=True) == [t2]
        assert t3.templates(local_only=False) == [t2, t1]

        # t1 is returned twice as it appears as a great-grandchild and a first class segment
        t4 = template.Template("t3", [t3, t1])
        assert t4.templates(local_only=True) == [t3, t1]
        assert t4.templates(local_only=False) == [t3, t2, t1, t1]

    def test_tokens(self):
        s_token = token.StringToken("str")
        i_token = token.IntToken("int")

        # No token segments should return an empty list
        t1 = template.Template("t1", ["abc", "1"])
        assert t1.tokens(local_only=True) == []
        assert t1.tokens(local_only=False) == []

        # s_token is a first level member of segments and should be in both
        t2 = template.Template("t2", [s_token, "_"])
        assert t2.tokens(local_only=True) == [s_token]
        assert t2.tokens(local_only=False) == [s_token]

        # s_token is returned twice as it appears as a grandchild and a first class segment
        t3 = template.Template("t3", [s_token, t2, i_token])
        assert t3.tokens(local_only=True) == [s_token, i_token]
        assert t3.tokens(local_only=False) == [s_token, s_token, i_token]
