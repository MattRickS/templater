class Case:
    Lower = "lower"
    LowerCamel = "lowerCamel"
    Upper = "upper"
    UpperCamel = "UpperCamel"


class TokenType:
    String = "str"
    Int = "int"


TEMPLATE_TYPE_PATH = "path"

DEFAULT_PADALIGN_INT = "="
DEFAULT_PADALIGN_STR = ">"
DEFAULT_PADCHAR_INT = "0"
DEFAULT_PADCHAR_STR = "X"

KEY_REGEX = "regex"
KEY_STRING = "string"
KEY_TEMPLATES = "templates"
KEY_TOKENS = "tokens"
KEY_TYPE = "type"

REGEX_INT = "[0-9]"
REGEX_STR = "[a-zA-Z]"

SYMBOL_TEMPLATE = "@"
SYMBOL_PATH_WILDCARD = "*"

TOKEN_PATTERN = r"{(\W)?([\w\.]+)}"
