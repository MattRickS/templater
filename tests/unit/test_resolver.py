import mock
import pytest

from template_resolver import exceptions, pathtemplate, resolver, template, token


@mock.patch("template_resolver.resolver.template")
@mock.patch("template_resolver.resolver.token")
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
                "root": "{str}_{int}",
                "parent": "{@root}_{str}",
                "example": "{lowerCase}_{int}",
                "name": "{@root}_{int_pad}",
            },
        }
    )
    str_token = mock_token_module.StringToken("str")
    int_token = mock_token_module.IntToken("int")
    int_pad_token = mock_token_module.IntToken(
        "int_pad", regex="[0-9]{3,}", format_spec="0=3d"
    )
    lower_case_token = mock_token_module.StringToken("lowerCase", "[a-z][a-zA-Z]+", "")

    root_template = mock_template_module.Template("root", [str_token, "_", int_token])
    parent_template = mock_template_module.Template(
        "parent", [root_template, "_", str_token]
    )
    example_template = mock_template_module.Template(
        "example", [lower_case_token, "_", int_token]
    )
    name_template = mock_template_module.Template(
        "name", [root_template, "_", int_pad_token]
    )

    assert resolver_obj._tokens == {
        "str": str_token,
        "int": int_token,
        "int_pad": int_pad_token,
        "lowerCase": lower_case_token,
    }
    assert resolver_obj._templates == {
        "root": root_template,
        "parent": parent_template,
        "example": example_template,
        "name": name_template,
    }


def test_get_template_cls():
    assert resolver.TemplateResolver.get_template_cls("template") == template.Template
    assert (
        resolver.TemplateResolver.get_template_cls("path") == pathtemplate.PathTemplate
    )

    with pytest.raises(exceptions.ResolverError):
        resolver.TemplateResolver.get_template_cls("unknown")


def test_get_token_cls():
    assert resolver.TemplateResolver.get_token_cls("int") == token.IntToken
    assert resolver.TemplateResolver.get_token_cls("str") == token.StringToken

    with pytest.raises(exceptions.ResolverError):
        resolver.TemplateResolver.get_token_cls("unknown")


@pytest.mark.parametrize(
    "tokens, templates, template_name, template_data, reference_config, expected",
    [
        (
            [token.StringToken("str"), token.IntToken("int")],
            [],
            "name",
            {"string": "/abc/{str}/{int}", "type": "template"},
            None,
            template.Template(
                "name", ["/abc/", token.StringToken("str"), "/", token.IntToken("int")]
            ),
        ),
        (
            [token.StringToken("str"), token.IntToken("int")],
            [template.Template("root", ["/root/", token.IntToken("int")])],
            "name",
            {"string": "{@root}/{str}", "type": "template"},
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
            {"string": "{@prefix}{str}", "type": "path"},
            {"prefix": {"string": "{int}_", "type": "template"}},
            pathtemplate.PathTemplate(
                "name",
                [
                    template.Template("prefix", [token.IntToken("int"), "_"]),
                    token.StringToken("str"),
                ],
            ),
        ),
    ],
)
def test_create_template(
    tokens, templates, template_name, template_data, reference_config, expected
):
    resolver_obj = resolver.TemplateResolver(tokens=tokens, templates=templates)
    template_obj = resolver_obj.create_template(
        template_name, template_data, reference_config=reference_config
    )
    assert repr(template_obj) == repr(expected)
    assert template_name in resolver_obj._templates
    assert resolver_obj._templates[template_name] == template_obj


def test_create_template__template_exists():
    resolver_obj = resolver.TemplateResolver(
        templates=[template.Template("name", ["string"])]
    )
    with pytest.raises(exceptions.ResolverError) as exc_info:
        resolver_obj.create_template(
            "name", {"string": "/root/{str}", "type": "template"}
        )
    assert str(exc_info.value) == "Template 'name' already exists"


def test_create_template__missing_token():
    resolver_obj = resolver.TemplateResolver()
    with pytest.raises(exceptions.ResolverError) as exc_info:
        resolver_obj.create_template("name", {"string": "/root/{str}", "type": "template"})
    assert str(exc_info.value) == "Requested token name does not exist: str"


def test_create_template__missing_template():
    resolver_obj = resolver.TemplateResolver()
    with pytest.raises(exceptions.ResolverError) as exc_info:
        resolver_obj.create_template("name", {"string": "/root/{@template}", "type": "template"})
    assert str(exc_info.value) == "Requested template name does not exist: template"


def test_create_template__invalid_symbol():
    resolver_obj = resolver.TemplateResolver()
    with pytest.raises(exceptions.ResolverError) as exc_info:
        resolver_obj.create_template("name", {"string": "/root/{!str}", "type": "template"})
    assert str(exc_info.value) == "Unknown token symbol: !"


@pytest.mark.parametrize(
    "name, config, expected",
    [
        (
            "int",
            {"type": "int"},
            token.IntToken("int", regex="[0-9]+", format_spec="d"),
        ),
        (
            "int_padded",
            {"type": "int", "padmin": 3},
            token.IntToken("int_padded", regex="[0-9]{3,}", format_spec="0=3d"),
        ),
        (
            "str",
            {"type": "str"},
            token.StringToken("str", regex="[a-zA-Z]+", format_spec="s"),
        ),
        (
            "str",
            {"type": "str", "padmax": 3},
            token.StringToken("str", regex="[a-zA-Z]{,3}", format_spec="s"),
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


def test_get_template():
    int_token = token.IntToken("int")
    str_token = token.StringToken("str")
    template_obj = template.Template("template", [str_token, "_", int_token])
    resolver_obj = resolver.TemplateResolver(
        tokens=[int_token], templates=[template_obj]
    )
    assert resolver_obj.get_template("template") == template_obj

    with pytest.raises(exceptions.ResolverError):
        resolver_obj.get_template("missing")


def test_get_token():
    int_token = token.IntToken("int")
    resolver_obj = resolver.TemplateResolver(tokens=[int_token])
    assert resolver_obj.get_token("int") == int_token

    with pytest.raises(exceptions.ResolverError):
        resolver_obj.get_token("missing")


def test_has_template():
    int_token = token.IntToken("int")
    str_token = token.StringToken("str")
    template_obj = template.Template("template", [str_token, "_", int_token])
    resolver_obj = resolver.TemplateResolver(
        tokens=[int_token], templates=[template_obj]
    )
    assert resolver_obj.has_template("template")
    assert not resolver_obj.has_template("missing")


def test_has_token():
    int_token = token.IntToken("int")
    resolver_obj = resolver.TemplateResolver(tokens=[int_token])
    assert resolver_obj.has_token("int")
    assert not resolver_obj.has_token("missing")
