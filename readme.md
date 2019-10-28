## Templates

Templates are defined as a list of segments. Each segment can be a fixed string, a token, or another template. Templates are used to format and parse strings using a dictionary of key, value pairs.

The same token can be used multiple times in a template, but when formatting or parsing the template, their value must always be the same for each instance.

## Tokens

Tokens represent a single pattern, such as a word or number. Tokens can be defined with a type so that values are converted correctly when parsing. Values formatted by the token must also be able to be parsed.

Tokens are defined by three key values:
* type : python datatype the token represents, eg, str, int
* regex : Regex pattern that's used to parse the token's string representation
* format_spec : Python format spec used to format the token's value into it's string representation

An additional field can be provided to tell users what the token should represent. This message is displayed as part of debug messages when failing to parse the token.
* description : A description of what the token should be, eg, "Must be a 3-digit integer". If not provided, a default is generated for all standard tokens.

If the regex and format_spec are not explicitly provided, common functionality can be constructed using separate keys. Providing any of the following keys with an explicit regex and/or format_spec will raise an error.
* padmin : Minimum number of characters in the token. This will set the format_spec to ensure provided values are padded to this length, and modify the regex to add a minimum requirement.
* padmax : Maximum number of characters the token can accept. This will modify the regex to add a maximum requirement.
* padchar : The additional character to add when padding out a sub-minimum string, modifies the format_spec. A default value is provided by standard tokens.
* padalign : The format_spec alignment character to use. A default value is provided by standard tokens.
* padstrict : boolean : If enabled, format_spec is not modified - insufficiently padding values are allowed to fail. Defaults to True for strings, and False for all others.
* choices : A fixed list of a values the token can have. If provided, format_spec and regex are overridden.

TODO: Add "choices" and "case"

## Subclassing

Custom tokens and templates can be defined and added as part of a custom resolver. The example below demonstrates how to add a custom template for templates with deprecated values, ie, a template with a removed token that needs to still parse the full set of values "{prefix}\_{key}\_{value}" -> "{key}\_{value}"

```python
from template_resolver import resolver, template


class DeprecatedTemplate(template.Template):
    def __init__(self, name, segments, static_fields=None):
        super(DeprecatedTemplate, self).__init__(name, segments)
        self.static_fields = static_fields or {}

    def extract(self, string):
        fields, end = super(DeprecatedTemplate, self).extract(string)
        fields.update(self.static_fields)
        return fields, end

    def parse(self, string):
        fields = super(DeprecatedTemplate, self).parse(string)
        fields.update(self.static_fields)
        return fields


class MyTemplateResolver(resolver.TemplateResolver):
    @classmethod
    def get_template_cls(cls, template_type):
        if template_type == "deprecated":
            template_cls = DeprecatedTemplate
        else:
            template_cls = super(MyTemplateResolver, cls).get_template_cls(
                template_type
            )
        return template_cls

    def create_template(self, template_name, template_config, reference_config=None):
        template_obj = super(MyTemplateResolver, self).create_template(
            template_name, template_config, reference_config=reference_config
        )
        if isinstance(template_obj, DeprecatedTemplate):
           template_obj.static_fields = template_config.get("static_fields")
        return template_obj


my_resolver = MyTemplateResolver()
my_resolver.create_token("key", {"type": "str"})
my_resolver.create_token("value", {"type": "str"})
my_template = my_resolver.create_template(
    "template",
    {
        "type": "deprecated",
        "string": "{key}_{value}",
        "static_fields": {"prefix": "pre"}
    }
)
my_template.parse("one_two")
# {"key": "one", "value": "two", "prefix": "pre"}
```
