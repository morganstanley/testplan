"""Arguments parsing utilities."""

import os
import argparse
import six
import itertools

USER_SPECIFIED_ARGS = '_user_specified_args'


class TestplanActionMeta(type):
    """
    When a derived action is called, the `__call__` function defined gets
    executed, and the value of `dest` in that action will be put into a set
    named `USER_SPECIFIED_ARGS`, which will be placed in the parsed result.
    """
    def __new__(cls, name, bases, attrs):
        if '__orig_call__' not in attrs:
            if '__call__' in attrs:
                attrs['__orig_call__'] = attrs['__call__']
            else:
                for base in itertools.chain(*[base.__mro__ for base in bases]):
                    call_func = getattr(base, '__orig_call__', None) or \
                                getattr(base, '__call__', None)
                    if call_func:
                        attrs['__orig_call__'] = call_func
                        break
                else:
                    err_msg = '__call__() not found in {} or its base classes'
                    raise TypeError(err_msg.format(name))

            def new_call_func(
                self, parser, namespace, values, option_string=None
            ):
                if not hasattr(namespace, USER_SPECIFIED_ARGS):
                    setattr(namespace, USER_SPECIFIED_ARGS, set())
                if self.dest is not argparse.SUPPRESS:
                    getattr(namespace, USER_SPECIFIED_ARGS).add(self.dest)
                self.__orig_call__(parser, namespace, values, option_string)

            attrs['__call__'] = new_call_func

        return super(TestplanActionMeta, cls).__new__(cls, name, bases, attrs)


@six.add_metaclass(TestplanActionMeta)
class TestplanAction(argparse.Action):
    """
    All customized actions for TestplanParser should inherit this class.
    """
    def __call__(self, parser, namespace, values, option_string=None):
        raise NotImplementedError('TestplanAction.__call__() not defined')


class ArgMixin(object):
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
            return cls[val.upper().replace('-', '_')]
        except KeyError:
            msg = 'Invalid value: `{}`, available values are: {}'.format(
                val,
                ', '.join(
                    ['`{}`'.format(cls.enum_to_str(enm)) for enm in cls]
                )
            )
            raise KeyError(msg)

    @classmethod
    def enum_to_str(cls, enm):
        """
        EnumClass.MY_ENUM -> `my-enum`
        """
        return enm.name.lower().replace('_', '-')

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

        help_strings.append('(default: {})'.format(default))

        if descriptions:
            for enm in cls:
                help_strings.append(
                    '"{}" - {}'.format(
                        cls.enum_to_str(enm), descriptions[enm]))

        return os.linesep.join(help_strings)

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
