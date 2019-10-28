import glob
import os

from template_resolver import constants, exceptions, template


class PathTemplate(template.Template):
    def extract_relative(self, path):
        """
        Args:
            path (str): Path to extract the template from

        Returns:
            tuple[dict, str]: Dictionary of fields extracted and the relative
                path remainder with leading separators stripped
        """
        agnostic_path = path.replace("\\", "/")
        fields, end = self.extract(agnostic_path)
        relative_path = agnostic_path[end:].lstrip("/")
        return fields, os.path.normpath(relative_path)

    def format(self, fields, unformatted=None, use_defaults=True):
        """
        Raises:
            exceptions.FormatError: If the fields don't match the template

        Args:
            fields (dict): Dictionary of fields to format the template with,
                must match tokens

        Keyword Args:
            unformatted (dict[str, str]): List of field names to skip formatting
                and use a wildcard symbol for
            use_defaults (bool): Whether or not to use token's default values
                for missing fields.

        Returns:
            str: OS path
        """
        path = super(PathTemplate, self).format(
            fields, unformatted=unformatted, use_defaults=use_defaults
        )
        return os.path.normpath(path)

    def parse(self, string):
        """
        Raises:
            exceptions.ParseError: If the string doesn't match the template
                exactly

        Args:
            string (str): String to parse the template tokens from

        Returns:
            dict: Dictionary of fields extracted from the tokens
        """
        agnostic_path = string.replace("\\", "/")
        return super(PathTemplate, self).parse(agnostic_path)

    def paths(self, fields, wildcards=None):
        """
        Args:
            fields (dict): Token names matched to values

        Keyword Args:
            wildcards (list[str]): List of field names to wildcard

        Returns:
            Iterable[tuple[dict, str]]: Iterable of matching paths and their
                fields
        """
        path_string = self.format(
            fields,
            unformatted={
                field: constants.SYMBOL_PATH_WILDCARD for field in wildcards or ()
            },
        )
        for path in glob.iglob(path_string):
            agnostic_path = path.replace("\\", "/")
            try:
                fields = self.parse(agnostic_path)
            except exceptions.ParseError:
                continue
            else:
                yield path, fields

    def root_template(self):
        """
        Returns:
            template.Template|None: Leading child template (if any)
        """
        first_segment = self._segments[0]
        if isinstance(first_segment, template.Template):
            return first_segment
