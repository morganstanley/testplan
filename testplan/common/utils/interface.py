"""Validates methods signature."""

from typing import Union, Optional
from inspect import signature


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


def check_signature(
    func: callable, args_list: Union[list, str]
) -> Optional[bool]:
    """
    Checks if the given function's signature matches the given list of args

    :param func: function whose signature to check
    :param args_list: list of arg names to match as signature

    :return: ``None`` or ``True``
    """

    funcparams = list(signature(func).parameters.keys())
    if funcparams != args_list:
        raise MethodSignatureMismatch(
            f"Expected {args_list}, not {funcparams} with {func}"
        )
    return True
