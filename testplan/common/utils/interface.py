"""Validates methods signature."""

from inspect import signature
from typing import Union


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


def check_signature(func: callable, args_list: Union[list, str]) -> bool:
    """
    Checks if the given function's signature matches the given list of args

    :param func: function whose signature to check
    :param args_list: list of arg names to match as signature

    :return: ``True`` if the signature is matching
    :raises MethodSignatureMismatch: if the given function's signature differs from the provided
    """
    funcparams = list(signature(func).parameters.keys())
    if funcparams != args_list:
        raise MethodSignatureMismatch(
            f"Expected arguments for {func.__name__} are {args_list}, not {funcparams}"
        )
    return True
