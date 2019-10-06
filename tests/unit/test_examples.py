import pytest

from template_resolver import exceptions, resolver, template, token


def test_template():
    token_a = token.StringToken("tokenA")
    token_b = token.StringToken("tokenB")
    token_c = token.IntToken("tokenC")
    example_template = template.Template(
        "templateA", ["/FIXED_STRING/", token_a, "/", token_b, token_c]
    )
    assert example_template.extract("/FIXED_STRING/abc/def1/banana") == (
        {"tokenA": "abc", "tokenB": "def", "tokenC": 1},
        22,
    )
    assert (
        example_template.format({"tokenA": "abc", "tokenB": "def", "tokenC": 1})
        == "/FIXED_STRING/abc/def1"
    )
    assert example_template.parse("/FIXED_STRING/abc/def1") == {
        "tokenA": "abc",
        "tokenB": "def",
        "tokenC": 1,
    }
    assert example_template.pattern() == "/FIXED_STRING/{tokenA}/{tokenB}{tokenC}"
    assert (
        example_template.pattern(formatters=True)
        == "/FIXED_STRING/{tokenA:s}/{tokenB:s}{tokenC:d}"
    )
    assert (
        example_template.regex()
        == r"\/FIXED_STRING\/(?P<tokenA>[a-zA-Z]+)\/(?P<tokenB>[a-zA-Z]+)(?P<tokenC>[0-9]+)"
    )
    assert example_template.tokens() == [token_a, token_b, token_c]

    token_d = token.StringToken("tokenD")
    parent_template = template.Template(
        "templateB", ["/start", example_template, "/", token_d, "/", token_a, "/end"]
    )
    assert (
        parent_template.format(
            {"tokenA": "abc", "tokenB": "def", "tokenC": 1, "tokenD": "ghi"}
        )
        == "/start/FIXED_STRING/abc/def1/ghi/abc/end"
    )
    assert parent_template.segments() == [
        "/start",
        "/FIXED_STRING/",
        token_a,
        "/",
        token_b,
        token_c,
        "/",
        token_d,
        "/",
        token_a,
        "/end",
    ]
    assert parent_template.segments(local_only=True) == [
        "/start",
        example_template,
        "/",
        token_d,
        "/",
        token_a,
        "/end",
    ]
    assert parent_template.tokens() == [token_a, token_b, token_c, token_d, token_a]
    assert parent_template.tokens(local_only=True) == [token_d, token_a]
    assert parent_template.templates() == [example_template]
    assert parent_template.fixed_strings() == [
        "/start",
        "/FIXED_STRING/",
        "/",
        "/",
        "/",
        "/end",
    ]
    assert parent_template.fixed_strings(local_only=True) == [
        "/start",
        "/",
        "/",
        "/end",
    ]


def test_resolver():
    t_resolver = resolver.TemplateResolver.from_config(
        {
            "tokens": {
                "str": "str",
                "int": "int",
                "int_pad": {"type": "int", "padmin": 3},
                "lowerCase": {"type": "str", "regex": "[a-z][a-zA-Z]+"},
            },
            "templates": {
                "root": "{str}_{int}",
                "parent": "{@root}_{str}",
                "example": "{lowerCase}_{int}",
                "name": "{@root}_{int_pad}",
            },
        }
    )
    assert repr(t_resolver.get_token("str")) == "StringToken('str', '[a-zA-Z]+', 's', description='Must be a string')"
    assert repr(t_resolver.get_token("int")) == "IntToken('int', '[0-9]+', 'd', description='Must be an integer')"

    lower_case_token = t_resolver.get_token("lowerCase")
    assert lower_case_token.format("abcDef") == "abcDef"
    with pytest.raises(exceptions.FormatError):
        lower_case_token.format("AbcDef")

    assert t_resolver.get_template("root").pattern() == "{str}_{int}"
    assert t_resolver.get_template("parent").pattern() == "{str}_{int}_{str}"
    assert (
        t_resolver.get_template("name").pattern(formatters=True)
        == "{str:s}_{int:d}_{int_pad:0=3d}"
    )
    assert (
        t_resolver.get_template("parent").format({"int": 50, "str": "abc"})
        == "abc_50_abc"
    )
    assert (
        t_resolver.get_template("example").format({"int": 50, "lowerCase": "abcDef"})
        == "abcDef_50"
    )
