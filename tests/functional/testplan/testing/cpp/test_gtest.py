import os
import platform

import pytest

from testplan import Testplan
from testplan.common.utils.testing import (
    log_propagation_disabled,
    check_report,
)
from testplan.common.utils.logger import TESTPLAN_LOGGER
from testplan.testing.cpp import GTest
from testplan.report import Status

from tests.functional.testplan.testing.fixtures.cpp import gtest

fixture_root = os.path.join(
    os.path.dirname(os.path.dirname(__file__)), "fixtures", "cpp", "gtest"
)

BINARY_NOT_FOUND_MESSAGE = """
Compiled test binary not found at: "{binary_path}", this test will be skipped.
You need to compile the files at "{binary_dir}" to be able to run this test.
"""


@pytest.mark.skipif(
    platform.system() == "Windows", reason="GTest is skipped on Windows."
)
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
def test_gtest(binary_dir, expected_report, report_status):

    binary_path = os.path.join(binary_dir, "runTests")

    if not os.path.exists(binary_path):
        msg = BINARY_NOT_FOUND_MESSAGE.format(
            binary_dir=binary_dir, binary_path=binary_path
        )
        pytest.skip(msg)

    plan = Testplan(name="plan", parse_cmdline=False)

    plan.add(GTest(name="MyGTest", driver=binary_path))

    with log_propagation_disabled(TESTPLAN_LOGGER):
        assert plan.run().run is True

    check_report(expected=expected_report, actual=plan.report)

    assert plan.report.status == report_status
