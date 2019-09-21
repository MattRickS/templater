import re

from template_resolver import constants, exceptions, template, token


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

        resolver_obj = cls()

        for token_name, token_data in token_config.items():
            if isinstance(token_data, str):
                token_data = {constants.KEY_TYPE: token_data}
            resolver_obj.create_token(token_name, token_data)

        for name, string in template_config.items():
            # Referenced templates may be already loaded by parent templates
            if not resolver_obj.has_template(name):
                resolver_obj.create_template(name, string, config=template_config)

        return resolver_obj

    def __init__(self, tokens=None, templates=None):
        """
        Args:
            tokens (Iterable[token.Token]): Iterable of unique token objects
            templates (Iterable[template.Template]): Iterable of unique template
                objects
        """
        # Must be created before the dict comprehension
        self._templates = {t.name: t for t in tokens or ()}
        self._tokens = {t.name: t for t in templates or ()}

    def create_template(self, template_name, template_string, config=None):
        """
        Raises:
            exceptions.ResolverError: If the template string references a
                non-existent value

        Args:
            template_name (str): Name of the template to create
            template_string (str): String representing the template

        Keyword Args:
            config (dict): Dictionary of template names mapped to template
                strings. If creating a template which references additional
                templates that does not exist yet, the resolver will try to
                recursively construct templates from the config.

        Returns:
            template.Template: Created template object stored in the resolver
        """
        if template_name in self._templates:
            raise exceptions.ResolverError(
                "Template {!r} already exists".format(template_name)
            )

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
            if symbol == constants.SYMBOL_PATH_TEMPLATE:
                template_obj = self._templates.get(name)
                if template_obj is None:
                    ref_string = config.get(name)
                    if ref_string is None:
                        raise exceptions.ResolverError(
                            "Template {!r} required by {!r} does not exist".format(
                                name, template_name
                            )
                        )
                    template_obj = self.create_template(name, ref_string, config=config)
                segments.append(template_obj)
            elif not symbol:
                token_obj = self.get_token(name)
                segments.append(token_obj)
            else:
                raise exceptions.ResolverError(
                    "Unknown token symbol: {}".format(symbol)
                )

        template_obj = template.Template(template_name, segments)
        self._templates[template_name] = template_obj
        return template_obj

    def create_token(self, token_name, token_data):
        """
        Raises:
            exceptions.ResolverError: If the token data is invalid

        Args:
            token_name (str): Name of the token to create
            token_data (dict): Dictionary of token data, with a minimum of a
                "type" key.

        Returns:
            token.Token: Created token object stored in the resolver
        """
        if token_name in self._tokens:
            raise exceptions.ResolverError(
                "Token {!r} already exists".format(token_name)
            )

        token_type = token_data[constants.KEY_TYPE]
        token_regex = token_data.get(constants.KEY_REGEX)
        if token_type == constants.TokenType.Int:
            token_cls = token.IntToken
        elif token_type == constants.TokenType.String:
            token_cls = token.StringToken
        else:
            raise exceptions.ResolverError("Unknown token type: {}".format(token_type))

        token_obj = (
            token_cls(token_name, regex=token_regex)
            if token_regex
            else token_cls(token_name)
        )
        self._tokens[token_name] = token_obj
        return token_obj

    def get_template(self, name):
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
                "Referenced template name does not exist: {}".format(name)
            )
        return template_obj

    def get_token(self, name):
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
                "Referenced template name does not exist: {}".format(name)
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
