class TokenType(object):
    String = "str"
    Custom = "custom"
    Int = "int"


KEY_REGEX = "regex"
KEY_TEMPLATES = "templates"
KEY_TOKENS = "tokens"
KEY_TYPE = "type"

SYMBOL_PATH_TEMPLATE = "@"
TOKEN_PATTERN = "{{({})?(\w+)}}".format(SYMBOL_PATH_TEMPLATE)
