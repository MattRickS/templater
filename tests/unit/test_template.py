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
        assert t.segments == ["abc", "def"]

        # Should return a copy, original should be unmodified
        t.segments[0] = "ghi"
        assert t.segments == ["abc", "def"]

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

    def test_format(self):
        t = template.Template("name", ["abc", token.IntToken("int"), "def"])
        assert t.format({"abc": 1}) == "abc1def"

    def test_parse(self):
        pass

    def test_pattern(self):
        pass

    def test_regex(self):
        pass

    def test_templates(self):
        pass

    def test_tokens(self):
        pass
