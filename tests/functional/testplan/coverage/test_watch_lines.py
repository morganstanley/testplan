from pathlib import Path
import random
import tempfile

# to avoid "testsuite" & "testcase" treated as tests by pytest
import testplan.testing.multitest as mt
from testplan import TestplanMock

from subject_module import (
    box,
    lazy_apply,
    lazy_get,
    lazy_len,
    lazy_zip_with,
    to_lazy,
    unbox,
    unlazy,
)


@mt.testsuite
class BasicSuite:
    @mt.testcase
    def simple_case(self, env, result):
        li = [2, 3, 5]
        result.equal(unlazy(to_lazy(li)), li)

    @mt.testcase(
        parameters={
            "li": [[random.randint(1, 50) for _ in range(5)] for _ in range(5)]
        }
    )
    def parameterized_case(self, env, result, li):
        result.equal(unlazy(to_lazy(li)), li)

    @mt.testcase(
        parameters={
            "lli1": [to_lazy([None, None, 2, None])],
            "lli2": [to_lazy([NotImplemented, None, 4, NotImplemented])],
        }
    )
    def parameter_only_case(self, env, result, lli1, lli2):
        lli = lazy_zip_with(lambda x, y: x * y, lli1, lli2)
        result.equal(unbox(lazy_get(lli, 2)), 8)


@mt.testsuite
class ParallelSuite:
    @mt.testcase
    def simple_case(self, env, result):
        lli1 = to_lazy([1, 2, 3])
        lli2 = to_lazy([2, 3])

        def _(x, y):
            raise NotImplementedError("welp")

        result.equal(lazy_len(lazy_zip_with(_, lli1, lli2)), 2)

    @mt.testcase(
        parameters={
            "li": [[random.randint(1, 50) for _ in range(5)] for _ in range(5)]
        },
        execution_group="group_1",
    )
    def parallel_parametrized_case(self, env, result, li):
        result.equal(unlazy(to_lazy(li)), li)


@mt.testsuite
class WithPrePostSuite:
    ...


@mt.testsuite
class WithSetupTeardownSuite:
    ...


def multitest_before_start():
    _ = to_lazy([1, 2, 3])


def multitest_after_stop():
    _ = lazy_apply(
        lambda x, y: x / y, box(NotImplemented), box(NotImplemented)
    )


def test_watch_lines_basic():
    with tempfile.NamedTemporaryFile(mode="w+") as f:

        plan = TestplanMock(
            name="watch_lines_test",
            watching_lines={
                str(
                    Path(__file__)
                    .parent.joinpath("subject_module.py")
                    .resolve()
                ): [26, 27, 28, 29]
            },
            impacted_tests_output=f.name,
        )
        plan.add(mt.MultiTest(name="BasicMultitest", suites=[BasicSuite()]))
        plan.run()

        lines = [
            *filter(lambda x: bool(x), map(lambda x: x.strip(), f.readlines()))
        ]
        assert lines[0] == "BasicMultitest:BasicSuite:simple_case"
        for i in range(1, 6):
            assert lines[i].startswith(
                "BasicMultitest:BasicSuite:parameterized_case:parameterized_case <li=["
            )
