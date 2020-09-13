import pytest

from templater import constants, exceptions, template, token, util


@pytest.mark.parametrize(
    "case, expected",
    [
        (constants.Case.Lower, "[a-z]"),
        (constants.Case.LowerCamel, "[a-z][a-zA-Z]"),
        (constants.Case.Upper, "[A-Z]"),
        (constants.Case.UpperCamel, "[A-Z][a-zA-Z]"),
    ],
)
def test_get_case_regex(case, expected):
    assert util.get_case_regex(case) == expected


def test_get_case_regex__invalid():
    with pytest.raises(exceptions.ResolverError) as exc_info:
        util.get_case_regex("invalid")
    assert str(exc_info.value) == "Unknown case: invalid"


@pytest.mark.parametrize(
    "padmin, padmax, expected",
    [(None, None, "+"), (3, None, "{3,}"), (None, 3, "{,3}"), (2, 5, "{2,5}")],
)
def test_get_regex_padding(padmin, padmax, expected):
    assert util.get_regex_padding(padmin=padmin, padmax=padmax) == expected


def test_get_regex_padding__invalid_range():
    with pytest.raises(exceptions.ResolverError) as exc_info:
        util.get_regex_padding(padmin=3, padmax=1)
    assert str(exc_info.value) == "Padmax (1) cannot be lower than padmin (3)"

    with pytest.raises(exceptions.ResolverError) as exc_info:
        util.get_regex_padding(padmin=-1)
    assert str(exc_info.value) == "Padmin cannot be less than 0: -1"

    with pytest.raises(exceptions.ResolverError) as exc_info:
        util.get_regex_padding(padmax=-2)
    assert str(exc_info.value) == "Padmax cannot be less than 0: -2"


@pytest.mark.parametrize(
    "string, expected_format",
    [
        (
            "seqSequence_shotShot",
            "Token 'shot' does not match: Must be a 3-digit integer\n"
            "Pattern: seq{sequence}_shot{shot}\n"
            "         seqSequence_shotShot\n"
            "                         ^",
        ),
        (
            "seqsequence_shot123",
            "Token 'sequence' does not match: Must be UpperCamel case\n"
            "Pattern: seq{sequence}_shot{shot}\n"
            "         seqsequence_shot123\n"
            "            ^",
        ),
        (
            "seqSequence_shot12",
            "Token 'shot' does not match: Must be a 3-digit integer\n"
            "Pattern: seq{sequence}_shot{shot}\n"
            "         seqSequence_shot12\n"
            "                         ^",
        ),
        (
            "seqSequence_shot12345",
            "Template matches string with remainder\n"
            "Pattern: seq{sequence}_shot{shot}\n"
            "         seqSequence_shot12345\n"
            "                            ^",
        ),
        (
            "SeqSequence_shot123",
            "String 'seq' does not match\n"
            "Pattern: seq{sequence}_shot{shot}\n"
            "         SeqSequence_shot123\n"
            "         ^",
        ),
        (
            "seqSequence_sot123",
            "String '_shot' does not match\n"
            "Pattern: seq{sequence}_shot{shot}\n"
            "         seqSequence_sot123\n"
            "                      ^",
        ),
    ],
)
def test_format_string_debugger(string, expected_format):
    t = template.Template(
        "name",
        [
            "seq",
            token.StringToken(
                "sequence",
                regex="[A-Z][a-zA-Z]+",
                description="Must be UpperCamel case",
            ),
            "_shot",
            token.IntToken(
                "shot", regex="[0-9]{3}", description="Must be a 3-digit integer"
            ),
        ],
    )
    with pytest.raises(exceptions.DebugParseError) as exc_info:
        t.parse_debug(string)
    assert util.format_string_debugger(t, string, exc_info.value) == expected_format
