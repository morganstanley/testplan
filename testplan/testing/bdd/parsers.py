import re
import parse
import abc


class Parser(object, metaclass=abc.ABCMeta):
    def match(self, sentence):
        pass

    def bind(self, func, mathc):
        pass


class RegExParser(Parser):
    """
    Parser implementation, matching regex on step sentences
    """

    def __init__(self, expression):
        # type: (str) -> RegExParser

        self.expression = re.compile(expression)

    def match(self, sentence):
        return self.expression.match(sentence)

    def bind(self, func, match):
        return lambda env, result, context, *args: func(
            env, result, context, *args, **match.groupdict()
        )


class SimpleParser(Parser):
    """
    Parser implementation, using parse library to simplify match strings
    """

    def __init__(self, format_string):
        self.parser = parse.compile(format_string, case_sensitive=True)

    def match(self, sentence):
        return self.parser.parse(sentence)

    def bind(self, func, match):
        return lambda env, result, context, *args: func(
            env, result, context, *args, **match.named
        )
