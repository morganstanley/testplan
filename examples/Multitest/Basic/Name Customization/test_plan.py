#!/usr/bin/env python
"""
    A Simple example to show how to customize name for test suite and testcase.
"""

from testplan import test_plan
from testplan.testing.multitest import testsuite, testcase, MultiTest


def suite_name_func(cls_name, suite):
    """Function to return a customized name for test suite"""
    return "{} -- {}".format(cls_name, suite.val)


def case_name_func(func_name, kwargs):
    """Function to return a customized name for parameterized testcase"""
    return "{} -- {}+{}={}".format(
        func_name, kwargs["a"], kwargs["b"], kwargs["expected"]
    )


@testsuite(name="A simple test suite")
class SimpleSuite(object):
    @testcase(name="An empty testcase")
    def test_example(self, env, result):
        pass

    @testcase(
        name="Parametrized testcases",
        parameters=((1, 2, 3), (1, 0, 1)),
        name_func=case_name_func,
    )
    def test_equal(self, env, result, a, b, expected):
        result.equal(a + b, expected, description="Equality test")


@testsuite(name=suite_name_func)
class ComplicatedSuite(object):
    def __init__(self, val):
        self.val = val

    @testcase(name="A testcase with one assertion")
    def test_less_than(self, env, result):
        result.less(self.val, 100, description="{} < 100".format(self.val))


@test_plan(name="Name customization example")
def main(plan):

    plan.add(
        MultiTest(
            "Name customization example",
            suites=[SimpleSuite(), ComplicatedSuite(1), ComplicatedSuite(2)],
        )
    )


if __name__ == "__main__":
    import sys

    sys.exit(not main())
