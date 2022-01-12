import os

import pytest

from testplan import TestplanMock
from testplan.common.utils.testing import (
    check_report,
    captured_logging,
    argv_overridden,
)
from testplan.common.utils.logger import TESTPLAN_LOGGER
from testplan.testing.cpp import HobbesTest

from tests.functional.testplan.testing.fixtures.cpp import hobbestest

from pytest_test_filters import skip_on_windows

fixture_root = os.path.join(
    os.path.dirname(os.path.dirname(__file__)), "fixtures", "cpp", "hobbestest"
)

BINARY_NOT_FOUND_MESSAGE = """
Hobbes test binary not found at: "{binary_path}", this test will be skipped.
You can either use the mock test binary or replace it with a link to the actual Hobbes test binary to run this test.
"""


@skip_on_windows(reason="HobbesTest is skipped on Windows.")
@pytest.mark.parametrize(
    "binary_dir, expected_report",
    (
        (
            os.path.join(fixture_root, "failing"),
            hobbestest.failing.report.expected_report,
        ),
        (
            os.path.join(fixture_root, "passing"),
            hobbestest.passing.report.expected_report,
        ),
    ),
)
def test_hobbestest(mockplan, binary_dir, expected_report):

    binary_path = os.path.join(binary_dir, "hobbes-test")

    if not os.path.exists(binary_path):
        msg = BINARY_NOT_FOUND_MESSAGE.format(
            binary_dir=binary_dir, binary_path=binary_path
        )
        pytest.skip(msg)

    mockplan.add(
        HobbesTest(
            name="My HobbesTest",
            binary=binary_path,
            tests=["Hog", "Net", "Recursives"],
        )
    )

    assert mockplan.run().run is True

    check_report(expected=expected_report, actual=mockplan.report)


@skip_on_windows(reason="HobbesTest is skipped on Windows.")
@pytest.mark.parametrize(
    "binary_dir, expected_output",
    (
        (
            os.path.join(fixture_root, "passing"),
            hobbestest.passing.report.expected_output,
        ),
    ),
)
def test_hobbestest_listing(binary_dir, expected_output):

    binary_path = os.path.join(binary_dir, "hobbes-test")
    cmdline_args = ["--list"]

    with argv_overridden(*cmdline_args):
        plan = TestplanMock(name="plan", parse_cmdline=True)

        with captured_logging(TESTPLAN_LOGGER) as log_capture:
            plan.add(
                HobbesTest(
                    name="My HobbesTest",
                    binary=binary_path,
                    tests=["Hog", "Net", "Recursives"],
                )
            )
            result = plan.run()
            print(log_capture.output)
            assert log_capture.output == expected_output
            assert len(result.test_report) == 0, "No tests should be run."


def test_hobbestest_custom_args():
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
        "HobbesTest",
        "test",
        "hobbes-test",
    )

    default_runner = HobbesTest(
        name="Default HobbesTest test", binary=binary_path
    )
    default_runner.run()

    assert default_runner.test_command() == default_runner._test_command()
    assert default_runner.list_command() == default_runner._list_command()

    basic_runner = HobbesTest(
        name="HobbesTest test with one pre and one post arg",
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

    extra_runner = HobbesTest(
        name="HobbesTest test with pre args and post args",
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
