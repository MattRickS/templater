# Templater

Templater is a tool for defining patterns that can be used to parse/format strings. There are three main objects; Token, Template, TemplateResolver. These are briefly explained here, and further detail given below the examples.
* Tokens represent an unknown value to be parsed/formatted.
* Templates are a list of "segments", where each segment can be a fixed string, token, or another template.
* TemplateResolver is a manager class for constructing templates from a set of known tokens, or building templates from a configuration file.

## Examples
Basic templates can be constructed from the template and token modules
```python
from templater import template, token
```

Templates are just a sequence of "segments", where a segment can be a fixed string, token, or even another template.
```python
introduction = template.Template("introduction", ["My name is ", token.StringToken("name")])
string = introduction.format({"name": "Matt"})
fields = introduction.parse(string)
print(string, fields)
# My name is Matt {'name': 'Matt'}
```

Tokens have types and formatting so that parsing/formatting works with functional data.
```python
filename = template.Template("filename", [token.StringToken("name"), "_v", token.IntToken("version", format_spec="03d")])
fields = filename.parse("report_v001")
string = filename.format(fields)
print(string, fields)
# report_v001 {'name': 'report', 'version': 1}
```

Path templates have additional convenience methods for extracting relative paths and globbing the filesystem.
```python
from templater import pathtemplate, token
yearly_report_dir = pathtemplate.PathTemplate("yearly_report_dir", ["/root/", token.StringToken("project"), "/", token.IntToken("year", regex="\d{4}")])
fields, relative = yearly_report_dir.extract_relative("/root/sales/2020/report.txt")
print(fields, relative)
# {'project': 'sales', 'year': 2020} report.txt
paths = yearly_report_dir.paths({"project": "sales"}, wildcards=["year"])
print(list(paths))
# ['/root/sales/2018', '/root/sales/2019', '/root/sales/2020']
```

Incompatible matches raise a basic error, but more accurate error reporting can be achieved if required. A utility exists for formatting the DebugParseError for display.
```python
from templater import template, token, util, exceptions
mytemplate = template.Template("mytemplate", ["Year: ", token.IntToken("year")])
string = "Year: Friday"
# mytemplate.parse(string)  # exceptions.ParseError("String 'Year: Friday' doesn't match template 'mytemplate:Year: {year}'")
try:
    mytemplate.parse_debug(string)
except exceptions.DebugParseError as e:
    error = util.format_string_debugger(mytemplate, string, e)

print(error)
# Token 'year' does not match: 
# Pattern: Year: {year}
#          Year: Friday
#                ^
```

Templates can be configuration defined and managed by a TemplateResolver. Templates are grouped by mostly arbitrary types, which allows reusing a template name for different uses as well as overriding the Template class to use. The default package only provides one override type; templates defined under "path" use the PathTemplate.

Segments are referenced using bracketed syntax, eg, `{segmentname}`. The name in the brackets references a token unless it's preceeded by an `@` symbol in which case it references a template, eg, `{@templatename}`. The template name is looked up within the same template group. To reference a template from another group (or to be explicit), prefix with a group name and a `.` separator, eg, `{@group.templatename}`.
```python
from templater import resolver
manager = resolver.TemplateResolver.from_config(
    {
        "tokens": {
            "name": "str",
            "age": "int",
            "hobby": "str",
        },
        "templates": {
            "foo": {
                "intro": "{name} is {age} years old"
            },
            "bar": {
                "extended_into": "{@foo.intro}. He likes to {hobby}."
            }
        },
    }
)
intro = manager.template("foo", "intro")
fields = intro.parse("Tim is 3 years old")
extended_into = manager.template("bar", "extended_into")
fields["age"] += 2
fields["hobby"] = "swim"
extended_into.format(fields)
# 'Tim is 5 years old. He likes to swim.'
```

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

When constructing from a configuration, if the regex and format_spec are not explicitly provided common functionality can be constructed using separate keys. Providing any of the following keys with an explicit regex and/or format_spec will raise an error.
* padmin : Minimum number of characters in the token. This will set the format_spec to ensure provided values are padded to this length, and modify the regex to add a minimum requirement.
* padmax : Maximum number of characters the token can accept. This will modify the regex to add a maximum requirement.
* padchar : The additional character to add when padding out a sub-minimum string, modifies the format_spec. A default value is provided by standard tokens.
* padalign : The format_spec alignment character to use. A default value is provided by standard tokens.
* padstrict : boolean : If enabled, format_spec is not modified - insufficiently padding values are allowed to fail. Defaults to True for strings, and False for all others.
* choices : A fixed list of a values the token can have. If provided, format_spec and regex are overridden.

## Extending templates

Custom tokens and templates can be defined and added as part of a custom resolver. To support this, configuration allows providing a dictionary to each template key and uses the "string" key as the template pattern, passing any additional keywords to the `construct_template` method.

The example below demonstrates how to add a custom template for templates with deprecated values, ie, a template with a removed token that needs to still parse the full set of values "{prefix}\_{key}\_{value}" -> "{key}\_{value}".

```python
from templater import resolver, template


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
    def construct_template(cls, template_type, name, segments, **kwargs):
        if "static_fields" in kwargs:
            return DeprecatedTemplate(name, segments, static_fields=static_fields)
        else:
            return super().construct_template(template_type, name, segments, **kwargs)


my_resolver = MyTemplateResolver()
my_resolver.create_token("key", {"type": "str"})
my_resolver.create_token("value", {"type": "str"})
my_template = my_resolver.create_template(
    "template", "custom", "{key}_{value}", static_fields={"prefix": "pre"}
)
my_template.parse("one_two")
# {"key": "one", "value": "two", "prefix": "pre"}
```

## Tests

Test suite included requires pip installing the `requirements.test.in` file.
