import glob
import os
from typing import Any, Dict, Iterable, List, Tuple, Union

from templater import constants, exceptions, template


class PathTemplate(template.Template):
    def extract_relative(self, path: str) -> Tuple[Dict[str, Any], str]:
        """
        Args:
            path: Path to extract the template from

        Returns:
            Dictionary of fields extracted and the relative path remainder with
                leading separators stripped
        """
        agnostic_path = path.replace("\\", "/")
        fields, end = self.extract(agnostic_path)
        relative_path = agnostic_path[end:].lstrip("/")
        return fields, os.path.normpath(relative_path)

    def format(
        self, fields: Dict[str, Any], unformatted: Dict[str, str] = None, use_defaults: bool = True
    ) -> str:
        """
        Raises:
            exceptions.FormatError: If the fields don't match the template

        Args:
            fields: Dictionary of fields to format the template with, must match
                tokens

        Keyword Args:
            unformatted: List of field names to skip formatting and use a
                wildcard symbol for
            use_defaults: Whether or not to use token's default values for
                missing fields.

        Returns:
            OS path
        """
        path = super().format(fields, unformatted=unformatted, use_defaults=use_defaults)
        return os.path.normpath(path)

    def parse(self, string: str) -> Dict[str, Any]:
        """
        Raises:
            exceptions.ParseError: If the string doesn't match the template
                exactly

        Args:
            string: String to parse the template tokens from

        Returns:
            Dictionary of fields extracted from the tokens
        """
        agnostic_path = string.replace("\\", "/")
        return super().parse(agnostic_path)

    def paths(
        self, fields: Dict[str, Any], wildcards: List[str] = None
    ) -> Iterable[Tuple[Dict[str, Any], str]]:
        """
        Args:
            fields: Token names matched to values

        Keyword Args:
            wildcards: List of field names to wildcard

        Returns:
            Iterable of matching paths and their fields
        """
        path_string = self.format(
            fields,
            unformatted={field: constants.SYMBOL_PATH_WILDCARD for field in wildcards or ()},
        )
        for path in glob.iglob(path_string):
            agnostic_path = path.replace("\\", "/")
            try:
                fields = self.parse(agnostic_path)
            except exceptions.ParseError:
                continue
            else:
                yield path, fields

    def root_template(self) -> Union[template.Template, None]:
        """
        Returns:
            Leading child template (if any)
        """
        first_segment = self._segments[0]
        if isinstance(first_segment, template.Template):
            return first_segment
