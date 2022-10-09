from __future__ import annotations

import os
import re
from typing import Dict, Iterable, Type

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

        resolver_obj = cls()

        for token_name, token_data in token_config.items():
            if isinstance(token_data, str):
                token_data = {constants.KEY_TYPE: token_data}
            resolver_obj.create_token(token_name, token_data)

        for group, type_data in template_config.items():
            for name, template_string in type_data.items():
                # Referenced templates may be already loaded by parent templates
                if not resolver_obj.has_template(group, name):
                    kwargs = {}
                    if isinstance(template_string, dict):
                        kwargs = template_string
                        template_string = kwargs.pop(constants.KEY_STRING)
                    resolver_obj.create_template(
                        name,
                        group,
                        template_string,
                        reference_config=template_config,
                        **kwargs,
                    )

        return resolver_obj

    def _construct_template(self, group: str, name: str, segments, **kwargs) -> template.Template:
        """
        Args:
            group: Template group name
            name: Name of the template to create
            segments: List of segments in the template

        Keyword Args:
            kwargs: Any additional arguments to the class

        Returns:
            Constructed template
        """
        if group == constants.TEMPLATE_TYPE_PATH:
            token_cls = pathtemplate.PathTemplate
        else:
            token_cls = template.Template

        return token_cls(name, segments, **kwargs)

    def _construct_token(cls, token_type: str, name: str, token_config: dict) -> Type[token.Token]:
        """
        Args:
            token_type: String name of the token type
            token_config: Configuration for Token

        Returns:
            Token class the name represents
        """
        if token_type == constants.TokenType.Int:
            token_cls = token.IntToken
        elif token_type == constants.TokenType.String:
            token_cls = token.StringToken
        else:
            raise exceptions.ResolverError(f"Unknown token type: {token_type}")

        regex = token_cls.get_regex_from_config(token_config)
        format_spec = token_cls.get_format_spec_from_config(token_config)
        description = token_cls.get_description_from_config(token_config)
        default = token_config.get("default")
        return token_cls(
            name,
            regex=regex,
            format_spec=format_spec,
            description=description,
            default=default,
        )

    def __init__(
        self,
        tokens: Iterable[token.Token] = None,
        templates: Dict[str, Iterable[template.Template]] = None,
    ):
        """
        Args:
            tokens: Iterable of unique token objects
            templates: Iterable of unique template objects
        """
        self._tokens = {t.name: t for t in tokens or ()}
        self._templates = {
            group: {t.name: t for t in type_templates or ()}
            for group, type_templates in (templates or {}).items()
        }

    def create_template(
        self,
        template_name: str,
        group: str,
        string: str,
        reference_config: dict = None,
        **kwargs,
    ) -> template.Template:
        """
        Raises:
            exceptions.ResolverError: If the template string references a
                non-existent value

        Args:
            template_name: Name of the template to create
            group: Type of template to create
            string: String definition for the template

        Keyword Args:
            reference_config: Dictionary of template names mapped to
                template configs. If creating a template which references
                additional templates that does not exist yet, the resolver will
                try to recursively construct templates from this config.
            kwargs: Any additional keyword arguments to provide to the
                `construct_template` method.

        Returns:
            Created template object stored in the resolver
        """
        if self.has_template(group, template_name):
            raise exceptions.ResolverError(f"Template '{group}.{template_name}' already exists")

        # Template configuration can define environment variables
        template_string = os.path.expandvars(string)

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
                sep_index = name.find(".")
                if sep_index == -1:
                    subtype = group
                else:
                    subtype = name[:sep_index]
                    name = name[sep_index + 1 :]

                try:
                    template_obj = self.template(subtype, name)
                except exceptions.ResolverError:
                    ref_string = (reference_config or {}).get(subtype, {}).get(name)
                    if ref_string is None:
                        raise
                    template_obj = self.create_template(
                        name, subtype, ref_string, reference_config=reference_config
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

        template_obj = self._construct_template(group, template_name, segments, **kwargs)
        self._templates.setdefault(group, {})[template_name] = template_obj
        return template_obj

    def create_token(self, name: str, token_config: dict) -> token.Token:
        """
        Raises:
            exceptions.ResolverError: If the token data is invalid

        Args:
            name: Name of the token to create
            token_config: Dictionary of token data, with a minimum of a "type" key.

        Returns:
            Created token object stored in the resolver
        """
        if name in self._tokens:
            raise exceptions.ResolverError(f"Token '{name}' already exists")

        token_type = token_config[constants.KEY_TYPE]
        token_obj = self._construct_token(token_type, name, token_config)
        self._tokens[name] = token_obj
        return token_obj

    def template(self, group: str, name: str) -> template.Template:
        """
        Raises:
            exceptions.ResolverError: If no template exists matching the name

        Args:
            group: Type of template to get
            name: Name of the template to get
        """
        template_obj = self._templates.get(group, {}).get(name)
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

    def has_template(self, group: str, name: str) -> bool:
        """
        Args:
            group: Type of template
            name: Name of a template

        Returns:
            Whether or not the resolver has a template matching the name
        """
        return name in self._templates.get(group, ())

    def has_token(self, name: str) -> bool:
        """
        Args:
            name: Name of a token

        Returns:
            Whether or not the resolver has a token matching the name
        """
        return name in self._tokens
