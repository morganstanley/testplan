import json
import random

from testplan.testing.bdd.step_registry import step


class Indexable:
    def __getitem__(self, item):
        return self.__dict__[item]


class indexexample(Indexable):
    def __init__(self):
        self.a = 12
        self.b = 13
        self.l = [1, 2, 5]
        self.d = {"a": 12, "b": 13, "l": [1, 2, 5]}


@step("the example indexable is in the context as {name}")
def step_definition(env, result, context, name):
    context[name] = indexexample()


@step("{actual} == {expected}")
def step_definition(env, result, context, actual, expected):

    # note that this is string comparision as coming from the feature file
    result.equal(actual, expected)
