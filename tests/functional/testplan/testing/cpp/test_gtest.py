import os

import pytest

from testplan import TestplanMock
from testplan.common.utils.testing import check_report
from testplan.testing.cpp import GTest
from testplan.report import Status

from tests.functional.testplan.testing.fixtures.cpp import gtest

from pytest_test_filters import skip_on_windows

fixture_root = os.path.join(
    os.path.dirname(os.path.dirname(__file__)), "fixtures", "cpp", "gtest"
)

BINARY_NOT_FOUND_MESSAGE = """
Compiled test binary not found at: "{binary_path}", this test will be skipped.
You need to compile the files at "{binary_dir}" to be able to run this test.
"""


@skip_on_windows(reason="GTest is skipped on Windows.")
@pytest.mark.parametrize(
    "binary_dir, expected_report, report_status",
    (
        (
            os.path.join(fixture_root, "failing"),
            gtest.failing.report.expected_report,
            Status.FAILED,
        ),
        (
            os.path.join(fixture_root, "passing"),
            gtest.passing.report.expected_report,
            Status.PASSED,
        ),
        (
            os.path.join(fixture_root, "empty"),
            gtest.empty.report.expected_report,
            Status.PASSED,
        ),
    ),
)
def test_gtest(mockplan, binary_dir, expected_report, report_status):

    binary_path = os.path.join(binary_dir, "runTests")

    if not os.path.exists(binary_path):
        msg = BINARY_NOT_FOUND_MESSAGE.format(
            binary_dir=binary_dir, binary_path=binary_path
        )
        pytest.skip(msg)

    mockplan.add(GTest(name="My GTest", binary=binary_path))

    assert mockplan.run().run is True

    check_report(expected=expected_report, actual=mockplan.report)

    assert mockplan.report.status == report_status


@skip_on_windows(reason="GTest is skipped on Windows.")
def test_gtest_no_report(mockplan):

    binary_path = os.path.join(fixture_root, "error", "runTests.sh")

    mockplan.add(GTest(name="My GTest", binary=binary_path))

    assert mockplan.run().run is True
    assert mockplan.report.status == Status.ERROR
    assert "FileNotFoundError" in mockplan.report.flattened_logs[-1]["message"]


@skip_on_windows(reason="GTest is skipped on Windows.")
def test_gtest_xfail():
    plan = TestplanMock(
        name="GTest Xfail",
        xfail_tests={
            "Error GTest:*:*": {
                "reason": "GTest crash",
                "strict": True,
            },
            "Failing GTest:SquareRootTest:PositiveNos": {
                "reason": "known flaky",
                "strict": False,
            },
            "Failing GTest:SquareRootTestNonFatal:*": {
                "reason": "known flaky",
                "strict": False,
            },
        },
    )

    error_binary = os.path.join(fixture_root, "error", "runTests.sh")
    plan.add(GTest(name="Error GTest", binary=error_binary))

    failing_binary = os.path.join(fixture_root, "failing", "runTests")
    if os.path.exists(failing_binary):
        plan.add(GTest(name="Failing GTest", binary=failing_binary))

    assert plan.run().run is True

    assert plan.report.entries[0].status == Status.XFAIL

    if os.path.exists(failing_binary):
        assert (
            plan.report.entries[1].entries[0].entries[0].status == Status.XFAIL
        )
        assert plan.report.entries[1].entries[1].status == Status.XFAIL


def test_gtest_custom_args():
    pre_cmd = ["echo", '"Hi"']
    post_cmd = ["echo", '"Bye"']
    pre_cmds = pre_cmd + ["echo", "it's a pre arg"]
    post_cmds = post_cmd + ["echo", "it's a post arg"]

    binary_path = os.path.join(
        "..",
        "..",
        "..",
        "..",
        "..",
        "examples",
        "Cpp",
        "GTest",
        "test",
        "runTests",
    )

    default_runner = GTest(name="Default GTest test", binary=binary_path)
    default_runner.run()

    assert default_runner.test_command() == default_runner._test_command()
    assert default_runner.list_command() == default_runner._list_command()

    basic_runner = GTest(
        name="GTest test with one pre and one post arg",
        binary=binary_path,
        pre_args=pre_cmd,
        post_args=post_cmd,
    )
    basic_runner.run()

    assert (
        basic_runner.test_command()[0:2]
        == basic_runner.cfg._options["pre_args"]
    )
    assert (
        basic_runner.test_command()[-2:]
        == basic_runner.cfg._options["post_args"]
    )
    assert (
        basic_runner.list_command()[0:2]
        == basic_runner.cfg._options["pre_args"]
    )
    assert (
        basic_runner.list_command()[-2:]
        == basic_runner.cfg._options["post_args"]
    )

    extra_runner = GTest(
        name="GTest test with pre args and post args",
        binary=binary_path,
        pre_args=pre_cmds,
        post_args=post_cmds,
    )
    extra_runner.run()

    assert (
        extra_runner.test_command()[0:4]
        == extra_runner.cfg._options["pre_args"]
    )
    assert (
        extra_runner.test_command()[-4:]
        == extra_runner.cfg._options["post_args"]
    )
    assert (
        extra_runner.list_command()[0:4]
        == extra_runner.cfg._options["pre_args"]
    )
    assert (
        extra_runner.list_command()[-4:]
        == extra_runner.cfg._options["post_args"]
    )
