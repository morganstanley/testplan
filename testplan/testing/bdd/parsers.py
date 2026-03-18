import abc
import re
from typing import Any, Callable, Optional

import parse


class Parser(object, metaclass=abc.ABCMeta):
    @abc.abstractmethod
    def match(self, sentence: str) -> Any:
        pass

    @abc.abstractmethod
    def bind(self, func: Callable[..., Any], match: Any) -> Callable[..., Any]:
        pass


class RegExParser(Parser):
    """
    Parser implementation, matching regex on step sentences
    """

    def __init__(self, expression: str) -> None:
        self.expression = re.compile(expression)

    def match(self, sentence: str) -> Optional[re.Match[str]]:
        return self.expression.match(sentence)

    def bind(
        self, func: Callable[..., Any], match: re.Match[str]
    ) -> Callable[..., Any]:
        return lambda env, result, context, *args: func(
            env, result, context, *args, **match.groupdict()
        )


class SimpleParser(Parser):
    """
    Parser implementation, using parse library to simplify match strings
    """

    def __init__(self, format_string: str) -> None:
        self.parser = parse.compile(format_string, case_sensitive=True)

    def match(self, sentence: str) -> Any:
        return self.parser.parse(sentence)

    def bind(self, func: Callable[..., Any], match: Any) -> Callable[..., Any]:
        return lambda env, result, context, *args: func(
            env, result, context, *args, **match.named
        )
