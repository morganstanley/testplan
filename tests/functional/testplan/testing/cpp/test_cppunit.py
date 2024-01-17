import os

import pytest

from testplan.common.utils.testing import check_report
from testplan.testing.cpp import Cppunit
from testplan.common.report.base import Status

from tests.functional.testplan.testing.fixtures.cpp import cppunit

from pytest_test_filters import skip_on_windows

fixture_root = os.path.join(
    os.path.dirname(os.path.dirname(__file__)), "fixtures", "cpp", "cppunit"
)

BINARY_NOT_FOUND_MESSAGE = """
Compiled test binary not found at: "{binary_path}", this test will be skipped.
You need to compile the files at "{binary_dir}" to be able to run this test.
"""


@skip_on_windows(reason="Cppunit is skipped on Windows.")
@pytest.mark.parametrize(
    "binary_dir, expected_report, report_status",
    (
        (
            os.path.join(fixture_root, "failing"),
            cppunit.failing.report.expected_report,
            Status.FAILED,
        ),
        (
            os.path.join(fixture_root, "passing"),
            cppunit.passing.report.expected_report,
            Status.PASSED,
        ),
        (
            os.path.join(fixture_root, "empty"),
            cppunit.empty.report.expected_report,
            Status.PASSED,
        ),
    ),
)
def test_cppunit(mockplan, binary_dir, expected_report, report_status):

    binary_path = os.path.join(binary_dir, "runTests")

    if not os.path.exists(binary_path):
        msg = BINARY_NOT_FOUND_MESSAGE.format(
            binary_dir=binary_dir, binary_path=binary_path
        )
        pytest.skip(msg)

    mockplan.add(Cppunit(name="My Cppunit", binary=binary_path))

    assert mockplan.run().run is True

    check_report(expected=expected_report, actual=mockplan.report)

    assert mockplan.report.status == report_status


@skip_on_windows(reason="Cppunit is skipped on Windows.")
def test_cppunit_no_report(mockplan):

    binary_path = os.path.join(fixture_root, "error", "runTests.sh")

    mockplan.add(
        Cppunit(name="My Cppunit", binary=binary_path, file_output_flag="-y")
    )

    assert mockplan.run().run is True
    assert mockplan.report.status == Status.ERROR
    assert "FileNotFoundError" in mockplan.report.flattened_logs[-1]["message"]


def test_cppunit_custom_args():
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
        "Cppunit",
        "test",
        "runTests",
    )

    default_runner = Cppunit(name="Default cppunit test", binary=binary_path)
    default_runner.run()

    assert default_runner.test_command() == default_runner._test_command()
    assert not default_runner.list_command()

    default_runner = Cppunit(
        name="Default cppunit test", binary=binary_path, listing_flag="-l"
    )
    assert default_runner.list_command() == default_runner._list_command()

    basic_runner = Cppunit(
        name="Cppunit test with one pre and one post arg",
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
    assert not basic_runner.list_command()
    basic_runner = Cppunit(
        name="Cppunit test with one pre and one post arg",
        binary=binary_path,
        pre_args=pre_cmd,
        post_args=post_cmd,
        listing_flag="-l",
    )
    assert (
        basic_runner.list_command()[0:2]
        == basic_runner.cfg._options["pre_args"]
    )
    assert (
        basic_runner.list_command()[-2:]
        == basic_runner.cfg._options["post_args"]
    )

    extra_runner = Cppunit(
        name="Cppunit test with pre args and post args",
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
    assert not extra_runner.list_command()
    extra_runner = Cppunit(
        name="Cppunit test with pre args and post args",
        binary=binary_path,
        pre_args=pre_cmds,
        post_args=post_cmds,
        listing_flag="-l",
    )
    assert (
        extra_runner.list_command()[0:4]
        == extra_runner.cfg._options["pre_args"]
    )
    assert (
        extra_runner.list_command()[-4:]
        == extra_runner.cfg._options["post_args"]
    )
