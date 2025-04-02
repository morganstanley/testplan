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
        if arg_name.startswith("_"):
            return [arg_name]
        return [arg_name, f"_{arg_name}", "_"]
    return []


def check_signature(func: callable, args_list: List[str]) -> bool:
    """
    Checks if the given function's signature matches the given list of args

    :param func: function whose signature to check
    :param args_list: list of arg names to match as signature

    :return: ``True`` if the signature is matching
    :raises MethodSignatureMismatch: if the given function's signature differs from the provided
    """
    funcparams = [
        n
        for n, p in signature(func).parameters.items()
        if p.kind in (p.POSITIONAL_OR_KEYWORD, p.POSITIONAL_ONLY)
    ]

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


def check_signature_leading(func: callable, exp_params: List[str]) -> bool:
    """
    check if the leading (positional) parameters of the function signature
    matches the expected parameters
    this is for checking if parametrized testcases have been well defined
    """

    # return value is not very useful in this case, just to keep it consistent
    # with ``check_signature``

    funcparams = [
        n
        for n, p in signature(func).parameters.items()
        if p.kind in (p.POSITIONAL_OR_KEYWORD, p.POSITIONAL_ONLY)
    ]

    msg = (
        f"First several expected arguments for {func.__name__} are "
        f"{exp_params} or their underscore-prefixed variants, not "
        f"{funcparams[:len(exp_params)]}"
    )

    for exp in exp_params:
        if funcparams and funcparams[0] in _unused_variant(exp):
            funcparams.pop(0)
            continue
        break
    else:
        return True

    raise MethodSignatureMismatch(msg)
