import os
import platform

import pytest

from testplan.common.utils.testing import (
    log_propagation_disabled,
    check_report,
)
from testplan.common.utils.logger import TESTPLAN_LOGGER
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

    with log_propagation_disabled(TESTPLAN_LOGGER):
        assert mockplan.run().run is True

    check_report(expected=expected_report, actual=mockplan.report)

    assert mockplan.report.status == report_status
