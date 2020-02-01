import re

from template_resolver import constants, exceptions, pathtemplate, template, token


class TemplateResolver(object):
    @classmethod
    def from_config(cls, config):
        """
        Args:
            config (dict): Dictionary containing token and template definitions

        Returns:
            TemplateResolver: Resolver with the template configurations loaded
        """
        token_config = config[constants.KEY_TOKENS]
        template_config = config[constants.KEY_TEMPLATES]
        default_template_type = config.get(
            constants.KEY_DEFAULT_TEMPLATE_TYPE, constants.TemplateType.Standard
        )

        resolver_obj = cls()

        for token_name, token_data in token_config.items():
            if isinstance(token_data, str):
                token_data = {constants.KEY_TYPE: token_data}
            resolver_obj.create_token(token_name, token_data)

        for name, template_data in template_config.items():
            # Referenced templates may be already loaded by parent templates
            if not resolver_obj.has_template(name):
                if isinstance(template_data, str):
                    template_data = {
                        constants.KEY_TYPE: default_template_type,
                        constants.KEY_STRING: template_data,
                    }
                resolver_obj.create_template(
                    name, template_data, reference_config=template_config
                )

        return resolver_obj

    @classmethod
    def get_template_cls(cls, template_type):
        """
        Args:
            template_type (str): String name of the template type

        Returns:
            Type[token.Template]: Template class the name represents
        """
        if template_type == constants.TemplateType.Standard:
            token_cls = template.Template
        elif template_type == constants.TemplateType.Path:
            token_cls = pathtemplate.PathTemplate
        else:
            raise exceptions.ResolverError(
                "Unknown template type: {}".format(template_type)
            )

        return token_cls

    @classmethod
    def get_token_cls(cls, token_type):
        """
        Args:
            token_type (str): String name of the token type

        Returns:
            Type[token.Token]: Token class the name represents
        """
        if token_type == constants.TokenType.Int:
            token_cls = token.IntToken
        elif token_type == constants.TokenType.String:
            token_cls = token.StringToken
        else:
            raise exceptions.ResolverError("Unknown token type: {}".format(token_type))

        return token_cls

    def __init__(self, tokens=None, templates=None):
        """
        Args:
            tokens (Iterable[token.Token]): Iterable of unique token objects
            templates (Iterable[template.Template]): Iterable of unique template
                objects
        """
        # Must be created before the dict comprehension
        self._templates = {t.name: t for t in templates or ()}
        self._tokens = {t.name: t for t in tokens or ()}

    def create_template(self, template_name, template_config, reference_config=None):
        """
        Raises:
            exceptions.ResolverError: If the template string references a
                non-existent value

        Args:
            template_name (str): Name of the template to create
            template_config (dict): Dictionary of template data with a minimum
                of a "type" and "string" key

        Keyword Args:
            reference_config (dict): Dictionary of template names mapped to
                template configs. If creating a template which references
                additional templates that does not exist yet, the resolver will
                try to recursively construct templates from this config.

        Returns:
            template.Template: Created template object stored in the resolver
        """
        if template_name in self._templates:
            raise exceptions.ResolverError(
                "Template '{}' already exists".format(template_name)
            )

        template_type = template_config[constants.KEY_TYPE]
        template_string = template_config[constants.KEY_STRING]

        index = 0
        segments = []
        for match in re.finditer(constants.TOKEN_PATTERN, template_string):
            # Extract fixed string segments between token/templates
            start, end = match.span()
            if start != index:
                segments.append(template_string[index:start])
            index = end

            # Find the matching referenced object
            symbol, name = match.groups()
            if symbol == constants.SYMBOL_TEMPLATE:
                try:
                    template_obj = self.template(name)
                except exceptions.ResolverError:
                    if reference_config is None or name not in reference_config:
                        raise
                    template_obj = self.create_template(
                        name, reference_config[name], reference_config=reference_config
                    )
                segments.append(template_obj)
            elif not symbol:
                token_obj = self.token(name)
                segments.append(token_obj)
            else:
                raise exceptions.ResolverError(
                    "Unknown token symbol: {}".format(symbol)
                )

        # If it ends with a fixed string, ensure the remainder is added
        last_string_segment = template_string[index:]
        if last_string_segment:
            segments.append(last_string_segment)

        template_cls = self.get_template_cls(template_type)
        template_obj = template_cls(template_name, segments)
        self._templates[template_name] = template_obj
        return template_obj

    def create_token(self, token_name, token_config):
        """
        Raises:
            exceptions.ResolverError: If the token data is invalid

        Args:
            token_name (str): Name of the token to create
            token_config (dict): Dictionary of token data, with a minimum of a
                "type" key.

        Returns:
            token.Token: Created token object stored in the resolver
        """
        if token_name in self._tokens:
            raise exceptions.ResolverError(
                "Token '{}' already exists".format(token_name)
            )

        token_type = token_config[constants.KEY_TYPE]
        token_cls = self.get_token_cls(token_type)
        regex = token_cls.get_regex_from_config(token_config)
        format_spec = token_cls.get_format_spec_from_config(token_config)
        description = token_cls.get_description_from_config(token_config)
        default = token_config.get("default")
        token_obj = token_cls(
            token_name,
            regex=regex,
            format_spec=format_spec,
            description=description,
            default=default,
        )

        self._tokens[token_name] = token_obj
        return token_obj

    def template(self, name):
        """
        Raises:
            exceptions.ResolverError: If no template exists matching the name

        Args:
            name (str): Name of the template to get

        Returns:
            template.Template:
        """
        template_obj = self._templates.get(name)
        if template_obj is None:
            raise exceptions.ResolverError(
                "Requested template name does not exist: {}".format(name)
            )
        return template_obj

    def token(self, name):
        """
        Raises:
            exceptions.ResolverError: If no token exists matching the name

        Args:
            name (str): Name of the token to get

        Returns:
            token.Token:
        """
        token_obj = self._tokens.get(name)
        if token_obj is None:
            raise exceptions.ResolverError(
                "Requested token name does not exist: {}".format(name)
            )
        return token_obj

    def has_template(self, name):
        """
        Args:
            name (str): Name of a template

        Returns:
            bool: Whether or not the resolver has a template matching the name
        """
        return name in self._templates

    def has_token(self, name):
        """
        Args:
            name (str): Name of a token

        Returns:
            bool: Whether or not the resolver has a token matching the name
        """
        return name in self._tokens
