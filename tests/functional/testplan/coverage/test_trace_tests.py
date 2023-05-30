import inspect
import os
import random
import tempfile

import pytest
import schema
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

# to avoid "testsuite" & "testcase" treated as tests by pytest
import testplan.testing.multitest as mt
from testplan import TestplanMock


def get_lines(symb):
    t = inspect.getsourcelines(symb)
    return list(range(t[1], len(t[0]) + t[1]))


@pytest.fixture
def named_temp_file():
    tmp_d = tempfile.mkdtemp()
    tmp_f = os.path.join(tmp_d, "tmp_file")
    with open(tmp_f, "w"):
        pass
    try:
        yield tmp_f
    finally:
        os.remove(tmp_f)
        os.rmdir(tmp_d)


@pytest.fixture(scope="module")
def subject_path():
    yield os.path.realpath(
        os.path.join(os.path.dirname(__file__), "subject_module.py")
    )


@mt.testsuite
class BasicSuite:
    @mt.testcase
    def basic_case(self, env, result):
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
    def basic_case(self, env, result):
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
    def pre_testcase(self, name, env, result):
        li = to_lazy([NotImplemented])
        result.equal(lazy_len(li), 1)

    def post_testcase(self, name, env, result):
        a = NotImplemented
        result.equal(unbox(box(a)), a)

    @mt.testcase
    def relevant_case(self, env, result):
        li = ["x", "y", "z", "w"]
        result.equal(unlazy(to_lazy(li)), li)

    @mt.testcase
    def irrelevant_case(self, env, result):
        result.isclose(99999, 100000, 0.01, 0)
        result.isclose(99999, 100000, 0, 10)


@mt.testsuite
class WithSetupTeardownSuite:
    def setup(self, env):
        env.payload = to_lazy(
            [RuntimeError("jaja"), RuntimeError("jajaja"), "jajajaja"]
        )

    @mt.testcase
    def basic_case(self, env, result):
        result.equal(len(unbox(lazy_get(env.payload, 2))), 8)

    def teardown(self, env):
        del env.payload


def multitest_before_start(env):
    _ = to_lazy([1, 2, 3])


def multitest_after_stop(env):
    _ = lazy_apply(
        lambda x, y: x / y, box(NotImplemented), box(NotImplemented)
    )


def test_trace_tests_invalid_input(subject_path):
    with pytest.raises(
        schema.SchemaError, match=r".*of type <class \\'list\\'>.*"
    ):
        _ = TestplanMock(
            name=f"{inspect.currentframe().f_code.co_name}_test",
            tracing_tests={subject_path: ["i", "am", "invalid"]},
        )

    with pytest.raises(
        schema.SchemaError, match=r".*value \"also invalid am i\".*"
    ):
        _ = TestplanMock(
            name=f"{inspect.currentframe().f_code.co_name}_test",
            tracing_tests={subject_path: "also invalid am i"},
        )


def test_trace_tests_basic(subject_path, named_temp_file):
    mt_name = "BasicMultitest"
    plan = TestplanMock(
        name=f"{inspect.currentframe().f_code.co_name}_test",
        tracing_tests={subject_path: get_lines(to_lazy)},
        tracing_tests_output=named_temp_file,
    )
    plan.add(mt.MultiTest(name=mt_name, suites=[BasicSuite()]))
    plan.run()

    with open(named_temp_file, "r") as f:
        lines = [l.strip() for l in f.readlines() if l]
    assert len(lines) == 6
    assert lines[0] == f"{mt_name}:BasicSuite:basic_case"
    for i in range(1, 6):
        assert lines[i].startswith(
            f"{mt_name}:BasicSuite:parameterized_case:parameterized_case <li=["
        )


def test_trace_tests_all_lines(subject_path, named_temp_file):
    mt_name = "AllLinesMultitest"
    plan = TestplanMock(
        name=f"{inspect.currentframe().f_code.co_name}_test",
        tracing_tests={subject_path: "*"},
        tracing_tests_output=named_temp_file,
    )
    plan.add(mt.MultiTest(name=mt_name, suites=[BasicSuite()]))
    plan.run()

    with open(named_temp_file, "r") as f:
        lines = [l.strip() for l in f.readlines() if l]
    assert len(lines) == 7
    assert lines[-1].startswith(
        f"{mt_name}:BasicSuite:parameter_only_case:parameter_only_case <lli1="
    )


def test_trace_tests_ignore_parallel(subject_path, named_temp_file):
    mt_name = "ParallelMultitest"
    plan = TestplanMock(
        name=f"{inspect.currentframe().f_code.co_name}_test",
        tracing_tests={subject_path: get_lines(to_lazy)},
        tracing_tests_output=named_temp_file,
    )
    plan.add(mt.MultiTest(name=mt_name, suites=[ParallelSuite()]))
    plan.run()

    with open(named_temp_file, "r") as f:
        lines = [l.strip() for l in f.readlines() if l]
    assert len(lines) == 1
    assert lines[0] == f"{mt_name}:ParallelSuite:basic_case"


def test_trace_tests_case_with_pre_post(subject_path, named_temp_file):
    mt_name = "WithPrePostMultitest"
    plan = TestplanMock(
        name=f"{inspect.currentframe().f_code.co_name}_test",
        tracing_tests={subject_path: get_lines(unlazy) + get_lines(to_lazy)},
        tracing_tests_output=named_temp_file,
    )
    plan.add(mt.MultiTest(name=mt_name, suites=[WithPrePostSuite()]))
    plan.run()

    with open(named_temp_file, "r") as f:
        lines = [l.strip() for l in f.readlines() if l]
    assert len(lines) == 2
    assert lines[0] == f"{mt_name}:WithPrePostSuite:relevant_case"
    assert lines[1] == f"{mt_name}:WithPrePostSuite:irrelevant_case"


def test_trace_tests_suite_with_setup_teardown(subject_path, named_temp_file):
    mt_name = "WithSetupTeardownMultitest"
    plan = TestplanMock(
        name=f"{inspect.currentframe().f_code.co_name}_test",
        tracing_tests={subject_path: get_lines(box) + get_lines(unbox)},
        tracing_tests_output=named_temp_file,
    )
    plan.add(mt.MultiTest(name=mt_name, suites=[WithSetupTeardownSuite()]))
    plan.run()

    with open(named_temp_file, "r") as f:
        lines = [l.strip() for l in f.readlines() if l]
    assert len(lines) == 2
    assert lines[0] == f"{mt_name}:WithSetupTeardownSuite"
    assert lines[1] == f"{mt_name}:WithSetupTeardownSuite:basic_case"


def test_trace_tests_multitest_with_hook(subject_path, named_temp_file):
    mt_name = "WithHookMultitest"
    plan = TestplanMock(
        name=f"{inspect.currentframe().f_code.co_name}_test",
        tracing_tests={subject_path: get_lines(lazy_apply)},
        tracing_tests_output=named_temp_file,
    )
    plan.add(
        mt.MultiTest(
            name=f"{mt_name}_1",
            suites=[ParallelSuite()],
            before_start=multitest_before_start,
        )
    )
    plan.add(
        mt.MultiTest(
            name=f"{mt_name}_2",
            suites=[WithPrePostSuite()],
            after_stop=multitest_after_stop,
        )
    )
    plan.run()

    with open(named_temp_file, "r") as f:
        lines = [l.strip() for l in f.readlines() if l]
    assert len(lines) == 2
    assert lines[0] == f"{mt_name}_1:ParallelSuite:basic_case"
    assert lines[1] == f"{mt_name}_2"
