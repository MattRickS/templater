class TokenType(object):
    String = "str"
    Int = "int"


class TemplateType(object):
    Standard = "template"
    Path = "path"


DEFAULT_PADALIGN_INT = "="
DEFAULT_PADALIGN_STR = ">"
DEFAULT_PADCHAR_INT = "0"
DEFAULT_PADCHAR_STR = "X"

KEY_DEFAULT_TEMPLATE_TYPE = "default_template_type"
KEY_REGEX = "regex"
KEY_STRING = "string"
KEY_TEMPLATES = "templates"
KEY_TOKENS = "tokens"
KEY_TYPE = "type"

REGEX_INT = "[0-9]"
REGEX_STR = "[a-zA-Z]"

SYMBOL_TEMPLATE = "@"
SYMBOL_WILDCARD = "*"

TOKEN_PATTERN = r"{(\W)?(\w+)}"
