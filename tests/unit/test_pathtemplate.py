import os

from template_resolver import pathtemplate, token


def test_extract_relative():
    template_obj = pathtemplate.PathTemplate(
        "name", ["/root/", token.StringToken("str")]
    )
    assert template_obj.extract_relative("/root/folder/filename.ext") == (
        {"str": "folder"},
        "filename.ext",
    )


def test_format():
    template_obj = pathtemplate.PathTemplate(
        "name", ["/root/", token.StringToken("str"), "/filename.ext"]
    )
    assert template_obj.format({"str": "folder"}) == os.path.normpath(
        "/root/folder/filename.ext"
    )


def test_parse():
    template_obj = pathtemplate.PathTemplate(
        "name", ["/root/", token.StringToken("str"), "/filename.ext"]
    )
    assert template_obj.parse("/root/folder/filename.ext") == {"str": "folder"}
    assert template_obj.parse("\\root\\folder\\filename.ext") == {"str": "folder"}


def test_paths(fs):
    paths = [
        (
            os.path.normpath("/root/folderA/v1/filename.ext"),
            {"str": "folderA", "version": 1},
        ),
        (
            os.path.normpath("/root/folderA/v2/filename.ext"),
            {"str": "folderA", "version": 2},
        ),
        (
            os.path.normpath("/root/folderA/v3/filename.ext"),
            {"str": "folderA", "version": 3},
        ),
        (
            os.path.normpath("/root/folderB/v1/filename.ext"),
            {"str": "folderB", "version": 1},
        ),
        (
            os.path.normpath("/root/folderB/v2/filename.ext"),
            {"str": "folderB", "version": 2},
        ),
        (
            os.path.normpath("/root/folderB/v3/filename.ext"),
            {"str": "folderB", "version": 3},
        ),
    ]
    for path, _ in paths:
        fs.create_file(path)

    template_obj = pathtemplate.PathTemplate(
        "name",
        [
            "/root/",
            token.StringToken("str"),
            "/v",
            token.IntToken("version"),
            "/filename.ext",
        ],
    )
    assert list(template_obj.paths({"str": "folderA"}, wildcards=["version"])) == paths[:3]
    assert list(template_obj.paths({"version": 3}, wildcards=["str"])) == [paths[2], paths[5]]
    assert list(template_obj.paths({}, wildcards=["str", "version"])) == paths


def test_root_template():
    child_template = pathtemplate.PathTemplate(
        "name", ["/root/", token.StringToken("str")]
    )
    parent_template = pathtemplate.PathTemplate(
        "name", [child_template, "/filename.ext"]
    )
    assert parent_template.root_template() == child_template

    relative_template = pathtemplate.PathTemplate(
        "name", ["/drive", child_template, "/filename.ext"]
    )
    assert relative_template.root_template() is None
