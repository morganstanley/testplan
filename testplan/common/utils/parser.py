"""Arguments parsing utilities."""

import os
import argparse


class ArgMixin:
    """
    Utility mixin that can be used with Enums for cmdline arg parsing.

    Supports:

        * 'kebab-case' <-> 'CONSTANT_NAME' conversion.
        * Custom parser logic that displays
          all available options on failure.
        * Pretty help text rendering for each option.
          (need to be used with `argparse.RawTextHelpFormatter`)
    """

    @classmethod
    def str_to_enum(cls, val):
        """
        `my-enum` -> EnumClass.MY_ENUM
        """
        try:
            return cls[val.upper().replace("-", "_")]
        except KeyError:
            msg = "Invalid value: `{}`, available values are: {}".format(
                val,
                ", ".join(
                    ["`{}`".format(cls.enum_to_str(enm)) for enm in cls]
                ),
            )
            raise KeyError(msg)

    @classmethod
    def enum_to_str(cls, enm):
        """
        EnumClass.MY_ENUM -> `my-enum`
        """
        return enm.name.lower().replace("_", "-")

    @classmethod
    def parse(cls, arg):
        """
        Get the enum for given cmdline arg in string form, display
        all available options when an invalid value is parsed.
        """
        try:
            return cls.str_to_enum(arg).value
        except KeyError as e:
            raise argparse.ArgumentTypeError(str(e))

    @classmethod
    def get_descriptions(cls):
        """
        Override this method to return a dictionary with Enums as keys
        and description strings as values.

        This will later on be rendered via `--help` command.
        """
        return {}

    @classmethod
    def get_help_text(cls, default):
        """Render help text in the 'arg-value': 'description' format."""
        descriptions = cls.get_descriptions()
        help_strings = []

        help_strings.append("(default: {})".format(default))

        if descriptions:
            for enm in cls:
                help_strings.append(
                    '"{}" - {}'.format(cls.enum_to_str(enm), descriptions[enm])
                )

        return "\n".join(help_strings)

    @classmethod
    def get_parser_context(cls, default=None, **kwargs):
        """
        Shortcut method for populating
        `Argparse.parser.add_argument` params.
        """
        return dict(
            type=cls.parse,
            default=default,
            help=cls.get_help_text(default=default),
            **kwargs
        )
