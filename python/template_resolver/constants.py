class TokenType(object):
    String = "str"
    Int = "int"


DEFAULT_PADALIGN_INT = "="
DEFAULT_PADALIGN_STR = ">"
DEFAULT_PADCHAR_INT = "0"
DEFAULT_PADCHAR_STR = "X"

KEY_REGEX = "regex"
KEY_TEMPLATES = "templates"
KEY_TOKENS = "tokens"
KEY_TYPE = "type"

REGEX_INT = "[0-9]"
REGEX_STR = "[a-zA-Z]"

SYMBOL_PATH_TEMPLATE = "@"
SYMBOL_WILDCARD = "*"
TOKEN_PATTERN = r"{(\W)?(\w+)}"
