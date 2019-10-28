import pytest

from template_resolver import exceptions, template, token


class TestTemplate(object):
    def test_repr(self):
        t = template.Template("name", ["abc", "def"])
        assert repr(t) == "Template('name', ['abc', 'def'])"

    def test_str(self):
        t = template.Template("name", ["abc", "def"])
        assert str(t) == "name:abcdef"

        t = template.Template("name", ["abc", token.IntToken("one")])
        assert str(t) == "name:abc{one}"

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
        "segments, string, expected_fields, expected_end",
        [
            (["abc", token.IntToken("int"), "def"], "abc1def12", {"int": 1}, 7),
            (
                [token.StringToken("str"), "_", token.IntToken("int")],
                "word_30",
                {"int": 30, "str": "word"},
                7,
            ),
            # Duplicates of a token must parse the same value
            (
                [token.IntToken("int"), "_", token.IntToken("int")],
                "1_1_x",
                {"int": 1},
                3,
            ),
            # Child template
            (
                [
                    template.Template("child", ["prefix_", token.StringToken("str")]),
                    "_",
                    token.IntToken("int"),
                ],
                "prefix_word_1_b",
                {"str": "word", "int": 1},
                13,
            ),
        ],
    )
    def test_extract(self, segments, string, expected_fields, expected_end):
        t = template.Template("name", segments)
        fields, end = t.extract(string)
        assert fields == expected_fields
        assert end == expected_end

    def test_extract_error(self):
        t = template.Template("name", ["abc", "def"])
        with pytest.raises(exceptions.ParseError):
            t.extract("abcghi")

    def test_extract_conflict_error(self):
        t1 = template.Template(
            "name", [token.IntToken("int"), "_", token.IntToken("int")]
        )
        with pytest.raises(exceptions.ParseError):
            t1.extract("1_2")

        # Child templates with token names that match the parent should be consistent
        t2 = template.Template("name", [token.IntToken("int"), "_", t1])
        with pytest.raises(exceptions.ParseError):
            t2.extract("1_2_2")

    def test_extract_invalid_segment_error(self):
        t = template.Template("name", ["abc", 1])
        with pytest.raises(TypeError):
            t.extract("abc1")

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
        "segments, fields, wildcards, expected",
        [
            (["abc", token.IntToken("int"), "def"], {"int": 1}, None, "abc1def"),
            (
                [token.StringToken("str"), "_", token.IntToken("int")],
                {"int": 30, "str": "word"},
                None,
                "word_30",
            ),
            # Duplicates of a token should use the same value
            (
                [token.IntToken("int"), "_", token.IntToken("int")],
                {"int": 1},
                None,
                "1_1",
            ),
            # Child template
            (
                [
                    template.Template("child", ["prefix_", token.StringToken("str")]),
                    "_",
                    token.IntToken("int"),
                ],
                {"str": "word", "int": 1},
                None,
                "prefix_word_1",
            ),
            # Wildcards
            (
                [token.IntToken("int"), "_", token.StringToken("str")],
                {"str": "word"},
                {"int": "*"},
                "*_word",
            ),
            # Defaults
            (
                [token.IntToken("int", default=1), "_", token.StringToken("str", default="abc")],
                {},
                None,
                "1_abc",
            ),
        ],
    )
    def test_format(self, segments, fields, wildcards, expected):
        t = template.Template("name", segments)
        assert t.format(fields, unformatted=wildcards) == expected

    def test_format_error(self):
        t = template.Template("name", [token.StringToken("str"), "_", 1])

        # 1 is an invalid segment
        with pytest.raises(TypeError):
            t.format({"str": "abc"})

    def test_format_missing_token_error(self):
        t = template.Template(
            "name", [token.StringToken("str"), "_", token.IntToken("int", default=1)]
        )

        with pytest.raises(exceptions.MissingTokenError) as exc_info:
            t.format({"str": "abc"}, use_defaults=False)
        assert exc_info.value.token_name == "int"

        with pytest.raises(exceptions.MissingTokenError) as exc_info:
            t.format({"int": 1})
        assert exc_info.value.token_name == "str"

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
            # Child template
            (
                [
                    template.Template("child", ["prefix_", token.StringToken("str")]),
                    "_",
                    token.IntToken("int"),
                ],
                "prefix_word_1",
                {"str": "word", "int": 1},
            ),
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

        # incomplete match has trailing string "def"
        with pytest.raises(exceptions.ParseError):
            t.parse("abc10def")

    def test_parse_token_conflict_error(self):
        t = template.Template(
            "name",
            [token.StringToken("str"), token.IntToken("int"), token.StringToken("str")],
        )

        # Both tokens called "str" must have the same value
        with pytest.raises(exceptions.ParseError):
            t.parse("abc1def")

    @pytest.mark.parametrize(
        "segments, string, expected_fields",
        [
            (
                [
                    token.StringToken("name"),
                    "_",
                    template.Template(
                        "other", [token.StringToken("word"), "_", token.IntToken("num")]
                    ),
                    "_",
                    token.StringToken("name"),
                ],
                "abc_def_1_abc",
                {"name": "abc", "word": "def", "num": 1},
            ),
            ([token.StringToken("name"), "def"], "abcdef", {"name": "abc"}),
        ],
    )
    def test_parse_debug(self, segments, string, expected_fields):
        t = template.Template("name", segments)
        assert t.parse_debug(string) == expected_fields

    @pytest.mark.parametrize(
        "string, expected_cls, expected_char_index, expected_segment_index, expected_fields",
        [
            ("1", exceptions.DebugParseError, 0, 0, {}),
            ("abc", exceptions.DebugParseError, 3, 1, {"name": "abc"}),
            ("abc_", exceptions.DebugParseError, 4, 2, {"name": "abc"}),
            (
                "abc_def1_1",
                exceptions.DebugParseError,
                7,
                3,
                {"name": "abc", "word": "def"},
            ),
            (
                "abc_def_ghi",
                exceptions.DebugParseError,
                8,
                4,
                {"name": "abc", "word": "def"},
            ),
            (
                "abc_def_1",
                exceptions.DebugParseError,
                9,
                5,
                {"name": "abc", "word": "def", "num": 1},
            ),
            (
                "abc_def_1_",
                exceptions.DebugParseError,
                10,
                6,
                {"name": "abc", "word": "def", "num": 1},
            ),
            (
                "abc_def_1_ghi",
                exceptions.MismatchTokenError,
                10,
                6,
                {"word": "def", "num": 1},
            ),
            (
                "abc_def_1_abc_ghi",
                exceptions.ExcessStringError,
                13,
                7,
                {"name": "abc", "word": "def", "num": 1},
            ),
        ],
    )
    def test_parse_debug_error_1(
        self,
        string,
        expected_cls,
        expected_char_index,
        expected_segment_index,
        expected_fields,
    ):
        t = template.Template(
            "name",
            [
                token.StringToken("name"),
                "_",
                template.Template(
                    "other", [token.StringToken("word"), "_", token.IntToken("num")]
                ),
                "_",
                token.StringToken("name"),
            ],
        )
        with pytest.raises(expected_cls) as exc_info:
            t.parse_debug(string)

        assert exc_info.value.char_index == expected_char_index
        assert exc_info.value.segment_index == expected_segment_index
        assert exc_info.value.fields == expected_fields

    @pytest.mark.parametrize(
        "string, expected_cls, expected_char_index, expected_segment_index, expected_fields",
        [
            ("1", exceptions.DebugParseError, 0, 0, {}),
            ("abc", exceptions.DebugParseError, 3, 1, {"name": "abc"}),
        ],
    )
    def test_parse_debug_error_2(
        self,
        string,
        expected_cls,
        expected_char_index,
        expected_segment_index,
        expected_fields,
    ):
        t = template.Template("name", [token.StringToken("name"), "def"])
        with pytest.raises(expected_cls) as exc_info:
            t.parse_debug(string)

        assert exc_info.value.char_index == expected_char_index
        assert exc_info.value.segment_index == expected_segment_index
        assert exc_info.value.fields == expected_fields

    @pytest.mark.parametrize(
        "string, expected_cls, expected_char_index, expected_segment_index, expected_fields",
        [
            ("abc_center_123", exceptions.DebugParseError, 11, 2, {"prefix": "abc"}),
            # Partial fixed string match
            ("abc_centre_def", exceptions.DebugParseError, 8, 1, {"prefix": "abc"}),
        ],
    )
    def test_parse_debug_error_3(
        self,
        string,
        expected_cls,
        expected_char_index,
        expected_segment_index,
        expected_fields,
    ):
        t = template.Template(
            "name",
            [token.StringToken("prefix"), "_center_", token.StringToken("suffix")],
        )
        with pytest.raises(expected_cls) as exc_info:
            t.parse_debug(string)

        assert exc_info.value.char_index == expected_char_index
        assert exc_info.value.segment_index == expected_segment_index
        assert exc_info.value.fields == expected_fields

    @pytest.mark.parametrize(
        "segments, formatters, expected",
        [
            (
                [
                    "abc_",
                    token.IntToken("int", format_spec="03d"),
                    ".def.",
                    token.StringToken("str"),
                ],
                False,
                "abc_{int}.def.{str}",
            ),
            (
                [
                    "abc_",
                    token.IntToken("int", format_spec="03d"),
                    ".def.",
                    token.StringToken("str"),
                ],
                True,
                "abc_{int:03d}.def.{str:s}",
            ),
            (
                [
                    token.StringToken("str"),
                    "_",
                    template.Template("template", ["v", token.IntToken("int")]),
                ],
                False,
                "{str}_v{int}",
            ),
        ],
    )
    def test_pattern(self, segments, formatters, expected):
        t = template.Template("name", segments)
        assert t.pattern(formatters=formatters) == expected

    def test_pattern_error(self):
        t = template.Template("name", ["abc_", token.IntToken("int"), ".def.", 1])
        # 1 is an invalid segment
        with pytest.raises(TypeError):
            t.pattern()

    @pytest.mark.parametrize(
        "segments, expected",
        [
            (
                ["abc_", token.IntToken("int"), ".def.", token.StringToken("str")],
                r"abc_(?P<int>[0-9]+)\.def\.(?P<str>[a-zA-Z]+)",
            ),
            (
                [token.IntToken("int"), "_", token.IntToken("int")],
                r"(?P<int>[0-9]+)_(?P=int)",
            ),
        ],
    )
    def test_regex(self, segments, expected):
        t = template.Template("name", segments)
        assert t.regex() == expected

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
