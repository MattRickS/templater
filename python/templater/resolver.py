from __future__ import annotations

import os
import re
from typing import Iterable, Type

from templater import constants, exceptions, pathtemplate, template, token


class TemplateResolver:
    @classmethod
    def from_config(cls, config: dict) -> TemplateResolver:
        """
        Args:
            config: Dictionary containing token and template definitions

        Returns:
            Resolver with the template configurations loaded
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
                # Template configuration can define environment variables
                template_data[constants.KEY_STRING] = os.path.expandvars(
                    template_data[constants.KEY_STRING]
                )
                resolver_obj.create_template(name, template_data, reference_config=template_config)

        return resolver_obj

    @classmethod
    def get_template_cls(cls, template_type: str) -> Type[template.Template]:
        """
        Args:
            template_type: String name of the template type

        Returns:
            Template class the name represents
        """
        if template_type == constants.TemplateType.Standard:
            token_cls = template.Template
        elif template_type == constants.TemplateType.Path:
            token_cls = pathtemplate.PathTemplate
        else:
            raise exceptions.ResolverError(f"Unknown template type: {template_type}")

        return token_cls

    @classmethod
    def get_token_cls(cls, token_type: str) -> Type[token.Token]:
        """
        Args:
            token_type: String name of the token type

        Returns:
            Token class the name represents
        """
        if token_type == constants.TokenType.Int:
            token_cls = token.IntToken
        elif token_type == constants.TokenType.String:
            token_cls = token.StringToken
        else:
            raise exceptions.ResolverError(f"Unknown token type: {token_type}")

        return token_cls

    def __init__(
        self, tokens: Iterable[token.Token] = None, templates: Iterable[template.Template] = None
    ):
        """
        Args:
            tokens: Iterable of unique token objects
            templates: Iterable of unique template objects
        """
        # Must be created before the dict comprehension
        self._templates = {t.name: t for t in templates or ()}
        self._tokens = {t.name: t for t in tokens or ()}

    # TODO: Replace template_config with args
    def create_template(
        self, template_name: str, template_config: dict, reference_config: dict = None
    ) -> template.Template:
        """
        Raises:
            exceptions.ResolverError: If the template string references a
                non-existent value

        Args:
            template_name: Name of the template to create
            template_config: Dictionary of template data with a minimum
                of a "type" and "string" key

        Keyword Args:
            reference_config: Dictionary of template names mapped to
                template configs. If creating a template which references
                additional templates that does not exist yet, the resolver will
                try to recursively construct templates from this config.

        Returns:
            Created template object stored in the resolver
        """
        if template_name in self._templates:
            raise exceptions.ResolverError(f"Template '{template_name}' already exists")

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
                raise exceptions.ResolverError(f"Unknown token symbol: {symbol}")

        # If it ends with a fixed string, ensure the remainder is added
        last_string_segment = template_string[index:]
        if last_string_segment:
            segments.append(last_string_segment)

        template_cls = self.get_template_cls(template_type)
        template_obj = template_cls(template_name, segments)
        self._templates[template_name] = template_obj
        return template_obj

    def create_token(self, token_name: str, token_config: dict) -> token.Token:
        """
        Raises:
            exceptions.ResolverError: If the token data is invalid

        Args:
            token_name: Name of the token to create
            token_config: Dictionary of token data, with a minimum of a "type" key.

        Returns:
            Created token object stored in the resolver
        """
        if token_name in self._tokens:
            raise exceptions.ResolverError(f"Token '{token_name}' already exists")

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

    def template(self, name: str) -> template.Template:
        """
        Raises:
            exceptions.ResolverError: If no template exists matching the name

        Args:
            name: Name of the template to get
        """
        template_obj = self._templates.get(name)
        if template_obj is None:
            raise exceptions.ResolverError(f"Requested template name does not exist: {name}")
        return template_obj

    def token(self, name: str) -> token.Token:
        """
        Raises:
            exceptions.ResolverError: If no token exists matching the name

        Args:
            name: Name of the token to get
        """
        token_obj = self._tokens.get(name)
        if token_obj is None:
            raise exceptions.ResolverError(f"Requested token name does not exist: {name}")
        return token_obj

    def has_template(self, name: str) -> bool:
        """
        Args:
            name: Name of a template

        Returns:
            Whether or not the resolver has a template matching the name
        """
        return name in self._templates

    def has_token(self, name: str) -> bool:
        """
        Args:
            name: Name of a token

        Returns:
            Whether or not the resolver has a token matching the name
        """
        return name in self._tokens
