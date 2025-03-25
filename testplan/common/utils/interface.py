"""Validates methods signature."""

from inspect import signature
from itertools import zip_longest
from typing import List, Optional


class MethodSignatureMismatch(Exception):
    """
    MethodSignatureMismatch Exception
    """

    pass


def _unused_variant(arg_name: Optional[str]) -> List[str]:
    """
    returns all linter acceptable variants of the given arg_name
    """
    if isinstance(arg_name, str):
        if arg_name.startswith("_") or arg_name == "self":
            return [arg_name]
        return [arg_name, f"_{arg_name}"]
    return []


def check_signature(func: callable, args_list: List[str]) -> bool:
    """
    Checks if the given function's signature matches the given list of args

    :param func: function whose signature to check
    :param args_list: list of arg names to match as signature

    :return: ``True`` if the signature is matching
    :raises MethodSignatureMismatch: if the given function's signature differs from the provided
    """
    funcparams = list(signature(func).parameters.keys())

    if not all(
        map(
            lambda x: x[0] in _unused_variant(x[1]),
            zip_longest(funcparams, args_list),
        )
    ):
        raise MethodSignatureMismatch(
            f"Expected arguments for {func.__name__} are {args_list} or their "
            f"underscore-prefixed variants, not {funcparams}"
        )
    return True


def check_signature_leading(func: callable, exp_args: List[str]):
    funcparams = list(signature(func).parameters.keys())
    msg = (
        f"First several expected arguments for {func.__name__} are {exp_args} "
        f"or their underscore-prefixed variants, not {funcparams[:len(exp_args)]}"
    )

    for exp in exp_args:
        if funcparams and funcparams[0] in _unused_variant(exp):
            funcparams.pop(0)
            continue
        break
    else:
        return

    raise MethodSignatureMismatch(msg)
