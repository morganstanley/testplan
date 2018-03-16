"""Validates methods signature."""

import inspect

from six.moves import zip_longest

from .callable import getargspec


class MethodSignature(object):
    """
    Encapsulates a method signature
    """
    def __init__(self, name, argspec, function):
        """
        Construct a method signature

        :param name: name
        :type name: C{str}
        :param argspec: argument specification
        :type argspec: ``ArgSpec``
        :param function: function
        :type function: ``func``
        """
        self.name = name
        self.argspec = argspec
        self.function = function

    def __eq__(self, rhs):
        """
        Equality match, name and argspec should match

        :param rhs: argspec to compare against
        :type rhs: :py:class:`MethodSignature`

        :return: True if self and rhs are equivalent, False otherwise
        :rtype: C{bool}
        """
        (lhs_args, lhs_varargs, lhs_keywords, _) = self.argspec
        (rhs_args, rhs_varargs, rhs_keywords, _) = rhs.argspec
        return ((self.name == rhs.name) and
                (lhs_args == rhs_args) and
                (lhs_varargs == rhs_varargs) and
                (lhs_keywords == rhs_keywords))

    def __ne__(self, rhs):
        """
        Non equality match, name or argspec should differ

        :param rhs: argspec to compare against
        :type rhs: :py:class:`MethodSignature`

        :return: False if self and rhs are equivalent, True otherwise
        :rtype: ``bool``
        """
        return not self.__eq__(rhs)

    def __str__(self):
        """
        String representation, useful when mismatches occur

        :return: string representation for the MethodSignature
        :rtype: ``str``
        """
        def args_with_defaults(args, defaults):
            """
            Args to string, with defaults inserted where appropriate

            :param args: arguments
            :type args: ``list``
            :param defaults: default value of arguments
            :type defaults: ``list``

            :return: string representation of the signature arguments
            :rtype: ``str``
            """
            def argument(arg, default):
                """
                Arg=Default pair if Default is present

                :param arg: argument name
                :type arg: ``str``
                :param default: default value for argument
                :type default: ``object``

                :return: string representation
                :rtype: ``str``
                """
                return '{0}={1}'.format(arg, default) if default else arg
            return ', '.join(reversed([argument(arg, default)
                                       for arg, default
                                       in zip_longest(
                    reversed(args),
                    reversed(defaults if defaults else []))]
                                      ))

        args = ''.join([
            args_with_defaults(self.argspec.args, self.argspec.defaults),
            ', *{0}'.format(
                self.argspec.varargs) if self.argspec.varargs else '',
            ', **{0}'.format(
                self.argspec.keywords) if self.argspec.keywords else ''
        ])

        return '{0}({1})'.format(self.name, args)

    def __repr__(self):
        return '<{}> - {}'.format(self.__class__.__name__, self.__str__())


def static_method(name, args, varargs=None, keywords=None, defaults=None):
    """
    Syntactic sugar for static_method signature definition in an interface contract

    :param name: method name
    :param args: method args
    :param varargs: method varargs
    :param keywords: method keywords
    :param defaults: method defaults

    :return: a method signature
    :rtype: :py:class:`MethodSignature`
    """
    return MethodSignature(name,
                           inspect.ArgSpec(args, varargs, keywords, defaults),
                           lambda x: x.__func__)


def method(name, args, varargs=None, keywords=None, defaults=None):
    """
    Syntactic sugar for static_method signature definition in an interface
    contract.

    :param name: method name
    :param args: method args
    :param varargs: method varargs
    :param keywords: method keywords
    :param defaults: method defaults

    :return: a method signature
    :rtype: :py:class:`MethodSignature`
    """
    return MethodSignature(name,
                           inspect.ArgSpec(['self'] + args, varargs,
                                           keywords, defaults),
                           lambda x: x)


class NoSuchMethodInClass(Exception):
    """
    NoSuchMethodInClass Exception
    """
    pass


class MethodSignatureMismatch(Exception):
    """
    MethodSignatureMismatch Exception
    """
    pass


def check_signature(func, args_list):
    """
    Checks if the given function's signature matches the given list of args

    :param func: function whose signature to check
    :type func: ``callable``
    :param args_list: list of arg names to match as signature
    :type args_list: ``list`` of ``str``

    :return: ``None``
    :rtype: ``NoneType``
    """
    refsig = static_method(func.__name__, args_list)
    actualsig = MethodSignature(func.__name__,
                                getargspec(func),
                                lambda x: x)
    if refsig != actualsig:
        raise MethodSignatureMismatch('Expected {0}, not {1}'.format(
            refsig, actualsig))
    return True
