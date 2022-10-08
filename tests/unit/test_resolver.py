import mock
import pytest

from templater import constants, exceptions, pathtemplate, resolver, template, token


@mock.patch("templater.resolver.template")
@mock.patch("templater.resolver.token")
def test_from_config(mock_token_module, mock_template_module):
    resolver_obj = resolver.TemplateResolver.from_config(
        {
            "tokens": {
                "str": "str",
                "int": "int",
                "int_pad": {"type": "int", "padmin": 3},
                "lowerCase": {"type": "str", "regex": "[a-z][a-zA-Z]+"},
            },
            "templates": {
                "string": {
                    "root": "{str}_{int}",
                    "parent": "{@root}_{str}",
                    "example": "{lowerCase}_{int}",
                    "name": "{@root}_{int_pad}",
                }
            },
        }
    )
    str_token = mock_token_module.StringToken("str")
    int_token = mock_token_module.IntToken("int")
    int_pad_token = mock_token_module.IntToken("int_pad", regex="[0-9]{3,}", format_spec="0=3d")
    lower_case_token = mock_token_module.StringToken("lowerCase", "[a-z][a-zA-Z]+", "")

    root_template = mock_template_module.Template("root", [str_token, "_", int_token])
    parent_template = mock_template_module.Template("parent", [root_template, "_", str_token])
    example_template = mock_template_module.Template("example", [lower_case_token, "_", int_token])
    name_template = mock_template_module.Template("name", [root_template, "_", int_pad_token])

    assert resolver_obj._tokens == {
        "str": str_token,
        "int": int_token,
        "int_pad": int_pad_token,
        "lowerCase": lower_case_token,
    }
    assert resolver_obj._templates == {
        "path": {},
        constants.TemplateType.String: {
            "root": root_template,
            "parent": parent_template,
            "example": example_template,
            "name": name_template,
        },
    }


def test_get_template_cls():
    assert resolver.TemplateResolver.get_template_cls("string") == template.Template
    assert resolver.TemplateResolver.get_template_cls("path") == pathtemplate.PathTemplate

    with pytest.raises(exceptions.ResolverError):
        resolver.TemplateResolver.get_template_cls("unknown")


def test_get_token_cls():
    assert resolver.TemplateResolver.get_token_cls("int") == token.IntToken
    assert resolver.TemplateResolver.get_token_cls("str") == token.StringToken

    with pytest.raises(exceptions.ResolverError):
        resolver.TemplateResolver.get_token_cls("unknown")


@pytest.mark.parametrize(
    "tokens, templates, template_name, template_type, string, reference_config, expected",
    [
        (
            [token.StringToken("str"), token.IntToken("int")],
            [],
            "name",
            constants.TemplateType.String,
            "/abc/{str}/{int}",
            None,
            template.Template(
                "name", ["/abc/", token.StringToken("str"), "/", token.IntToken("int")]
            ),
        ),
        (
            [token.StringToken("str"), token.IntToken("int")],
            [template.Template("root", ["/root/", token.IntToken("int")])],
            "name",
            constants.TemplateType.String,
            "{@root}/{str}",
            None,
            template.Template(
                "name",
                [
                    template.Template("root", ["/root/", token.IntToken("int")]),
                    "/",
                    token.StringToken("str"),
                ],
            ),
        ),
        (
            [token.StringToken("str"), token.IntToken("int")],
            [],
            "name",
            constants.TemplateType.Path,
            "{@prefix}{str}",
            {constants.TemplateType.Path: {"prefix": "{int}_"}},
            pathtemplate.PathTemplate(
                "name",
                [
                    pathtemplate.PathTemplate("prefix", [token.IntToken("int"), "_"]),
                    token.StringToken("str"),
                ],
            ),
        ),
    ],
)
def test_create_template(
    tokens, templates, template_name, template_type, string, reference_config, expected
):
    resolver_obj = resolver.TemplateResolver(tokens=tokens, string_templates=templates)
    template_obj = resolver_obj.create_template(
        template_name, template_type, string, reference_config=reference_config
    )
    assert repr(template_obj) == repr(expected)
    assert template_name in resolver_obj._templates[template_type]
    assert resolver_obj._templates[template_type][template_name] == template_obj


def test_create_template__template_exists():
    resolver_obj = resolver.TemplateResolver(
        string_templates=[template.Template("name", ["string"])]
    )
    with pytest.raises(exceptions.ResolverError) as exc_info:
        resolver_obj.create_template("name", "string", "/root/{str}")
    assert str(exc_info.value) == "Template 'name' already exists"


def test_create_template__missing_token():
    resolver_obj = resolver.TemplateResolver()
    with pytest.raises(exceptions.ResolverError) as exc_info:
        resolver_obj.create_template("name", "string", "/root/{str}")
    assert str(exc_info.value) == "Requested token name does not exist: str"


def test_create_template__missing_template():
    resolver_obj = resolver.TemplateResolver()
    with pytest.raises(exceptions.ResolverError) as exc_info:
        resolver_obj.create_template("name", "string", "/root/{@template}")
    assert str(exc_info.value) == "Requested template name does not exist: template"


def test_create_template__invalid_symbol():
    resolver_obj = resolver.TemplateResolver()
    with pytest.raises(exceptions.ResolverError) as exc_info:
        resolver_obj.create_template("name", "string", "/root/{!str}")
    assert str(exc_info.value) == "Unknown token symbol: !"


@pytest.mark.parametrize(
    "name, config, expected",
    [
        (
            "int",
            {"type": "int", "description": "example"},
            token.IntToken("int", regex="[0-9]+", format_spec="d", description="example"),
        ),
        (
            "int_padded",
            {"type": "int", "padmin": 3},
            token.IntToken(
                "int_padded",
                regex="[0-9]{3,}",
                format_spec="0=3d",
                description="Must be a minimum 3-digit integer",
            ),
        ),
        (
            "str",
            {"type": "str"},
            token.StringToken(
                "str",
                regex="[a-zA-Z]+",
                format_spec="s",
                description="Must be a string",
            ),
        ),
        (
            "str",
            {"type": "str", "padmax": 3},
            token.StringToken(
                "str",
                regex="[a-zA-Z]{,3}",
                format_spec="s",
                description="Must be a maximum 3-character string",
            ),
        ),
        (
            "str",
            {"type": "str", "choices": ["abc", "def", "ghi"]},
            token.StringToken(
                "str",
                regex="abc|def|ghi",
                format_spec="s",
                description="Must be one of: ['abc', 'def', 'ghi']",
            ),
        ),
    ],
)
def test_create_token(name, config, expected):
    resolver_obj = resolver.TemplateResolver()
    token_obj = resolver_obj.create_token(name, config)
    assert repr(token_obj) == repr(expected)
    assert name in resolver_obj._tokens
    assert resolver_obj._tokens[name] == token_obj


def test_create_token__already_exists():
    resolver_obj = resolver.TemplateResolver(tokens=[token.IntToken("int")])
    with pytest.raises(exceptions.ResolverError) as exc_info:
        resolver_obj.create_token("int", {"type": "int"})
    assert str(exc_info.value) == "Token 'int' already exists"


def test_create_token__invalid_config():
    resolver_obj = resolver.TemplateResolver()

    with pytest.raises(exceptions.ResolverError) as exc_info:
        resolver_obj.create_token("int", {"type": "abc"})
    assert str(exc_info.value) == "Unknown token type: abc"

    with pytest.raises(exceptions.ResolverError) as exc_info:
        resolver_obj.create_token("int", {"type": "int", "padmin": 3, "padmax": 2})
    assert str(exc_info.value) == "Padmax (2) cannot be lower than padmin (3)"

    with pytest.raises(exceptions.ResolverError) as exc_info:
        resolver_obj.create_token("str", {"type": "str", "regex": "[a-z]", "choices": ["a", "b"]})
    assert str(exc_info.value) == "Cannot use construction keywords with explicit regex"


def test_get_template():
    int_token = token.IntToken("int")
    str_token = token.StringToken("str")
    template_obj = template.Template("template", [str_token, "_", int_token])
    resolver_obj = resolver.TemplateResolver(tokens=[int_token], string_templates=[template_obj])
    assert resolver_obj.template(constants.TemplateType.String, "template") == template_obj

    with pytest.raises(exceptions.ResolverError):
        resolver_obj.template(constants.TemplateType.String, "missing")


def test_get_token():
    int_token = token.IntToken("int")
    resolver_obj = resolver.TemplateResolver(tokens=[int_token])
    assert resolver_obj.token("int") == int_token

    with pytest.raises(exceptions.ResolverError):
        resolver_obj.token("missing")


def test_has_template():
    int_token = token.IntToken("int")
    str_token = token.StringToken("str")
    template_obj = template.Template("template", [str_token, "_", int_token])
    resolver_obj = resolver.TemplateResolver(tokens=[int_token], string_templates=[template_obj])
    assert resolver_obj.has_template(constants.TemplateType.String, "template")
    assert not resolver_obj.has_template(constants.TemplateType.String, "missing")


def test_has_token():
    int_token = token.IntToken("int")
    resolver_obj = resolver.TemplateResolver(tokens=[int_token])
    assert resolver_obj.has_token("int")
    assert not resolver_obj.has_token("missing")
