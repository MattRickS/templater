import pytest

from template_resolver import exceptions, util


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
