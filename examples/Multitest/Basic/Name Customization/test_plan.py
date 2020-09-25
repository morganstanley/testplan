#!/usr/bin/env python
"""
    A Simple example to show how to customize name for test suite and testcase.
"""

from testplan import test_plan
from testplan.testing.multitest import testsuite, testcase, MultiTest


def _name_func(self, original_name):
    """Function to return a customized name for test suite"""
    return original_name + " - " + str(getattr(self, "val", "Default"))


@testsuite(custom_name="A simple test suite")
class SimpleSuite(object):
    @testcase(name="An empty testcase")
    def test_example(self, env, result):
        pass

    @testcase(name="Parametrized testcases", parameters=((1, 2, 3), (1, 0, 1)))
    def test_equal(self, env, result, a, b, expected):
        result.equal(a + b, expected, description="Equality test")


@testsuite(custom_name=_name_func)
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
