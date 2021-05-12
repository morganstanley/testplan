"""Validates methods signature."""

from itertools import zip_longest

from .callable import getargspec


class MethodSignature(object):
    """
    Encapsulates a method signature
    """

    def __init__(self, name, args, varargs=None, keywords=None, defaults=None):
        """
        Construct a MethodSignature.

        :param name: name
        :type name: ``str``
        :param args: list of argument names
        :type args: ``List[str]``
        :param varargs: name of * parameter
        :type varargs: ``Optional[str]``
        :param keywords: name of ** parameter
        :type keywords: ``Optional[str]``
        :param defaults: default arguments.
        :type defaults: ``list`` or ``NoneType``
        """
        self.name = name
        self.args = args
        self.varargs = varargs
        self.keywords = keywords

        if defaults is None:
            self.defaults = []
        else:
            self.defaults = defaults

    @classmethod
    def from_callable(cls, func):
        """
        Construct a MethodSignature from a callable.

        :param func: any callable object (function, method, class etc.)
        :return: new MethodSignature instance
        """
        argspec = getargspec(func)
        return cls(
            func.__name__,
            argspec.args,
            argspec.varargs,
            argspec.keywords,
            argspec.defaults,
        )

    def __eq__(self, rhs):
        """
        Equality match, name and argspec should match

        :param rhs: argspec to compare against
        :type rhs: :py:class:`MethodSignature`

        :return: True if self and rhs are equivalent, False otherwise
        :rtype: ``bool``
        """
        return (
            (self.name == rhs.name)
            and (self.args == rhs.args)
            and (self.varargs == rhs.varargs)
            and (self.keywords == rhs.keywords)
        )

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
                return "{0}={1}".format(arg, default) if default else arg

            return ", ".join(
                reversed(
                    [
                        argument(arg, default)
                        for arg, default in zip_longest(
                            reversed(args), reversed(defaults)
                        )
                    ]
                )
            )

        args = "".join(
            [
                args_with_defaults(self.args, self.defaults),
                ", *{0}".format(self.varargs) if self.varargs else "",
                ", **{0}".format(self.keywords) if self.keywords else "",
            ]
        )

        return "{0}({1})".format(self.name, args)

    def __repr__(self):
        return "<{}> - {}".format(self.__class__.__name__, self.__str__())


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

    :return: ``None`` or ``True``
    :rtype: ``NoneType`` or ``bool``
    """
    refsig = MethodSignature(func.__name__, args_list)
    actualsig = MethodSignature.from_callable(func)
    if refsig != actualsig:
        raise MethodSignatureMismatch(
            "Expected {0}, not {1}".format(refsig, actualsig)
        )
    return True
