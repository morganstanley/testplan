#!/usr/bin/env python
"""
A Simple example to show how to customize name for testsuite and testcase.
"""

from testplan import test_plan
from testplan.testing.multitest import testsuite, testcase, MultiTest


def suite_name_func(cls_name, suite):
    """Function to return a customized name for testsuite."""
    return "{} -- {}".format(cls_name, suite.val)


def case_name_func(func_name, kwargs):
    """Function to return a customized name for parameterized testcase."""
    return "{} ({}+{}={})".format(
        func_name, kwargs["a"], kwargs["b"], kwargs["expected"]
    )


# In @testcase decorator, ``name`` should be a normal string, it can be
# used with ``name_func`` for parametrized testcases. Refer to examples
# "../../Parametrization/test_plan.py"


@testsuite(name="A Simple Suite")
class SimpleSuite:
    def pre_testcase(self, name, env, result, kwargs):
        result.log('Before testcase "{}" run'.format(name))
        result.log("Extra arguments: {}".format(kwargs))

    def post_testcase(self, name, env, result, kwargs):
        result.log('After testcase "{}" run'.format(name))

    @testcase(name="A simple testcase")
    def test_example(self, env, result):
        result.equal(env.runtime_info.testcase.name, "A simple testcase")

    @testcase(
        name="Parametrized testcases",
        parameters=((1, 2, 3), (1, 0, 1)),
        name_func=case_name_func,
    )
    def test_equal(self, env, result, a, b, expected):
        result.equal(a + b, expected, description="Equality test")
        result.equal(
            env.runtime_info.testcase.name,
            case_name_func(
                "Parametrized testcases",
                {"a": a, "b": b, "expected": expected},
            ),
        )


# In @testsuite decorator, ``name`` can be a normal string or a callable
# receiving 2 arguments ``cls_name`` and ``suite``, the former is testsuite
# class name, and the latter is the instance of testsuite class. This can be
# used when multiple instances from the same testsuite class are added into
# one Multitest, and their names in the report can be made different.


@testsuite(name=suite_name_func)
class ComplicatedSuite:
    def __init__(self, val):
        self.val = val

    def pre_testcase(self, name, env, result):
        pass

    def post_testcase(self, name, env, result):
        pass

    @testcase(name="A testcase with one assertion")
    def test_less_than(self, env, result):
        result.less(self.val, 100, description="{} < 100".format(self.val))


# A multitest has one testsuite instance from ``SimpleSuite`` and 2 instances
# from ``ComplicatedSuite``.


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
