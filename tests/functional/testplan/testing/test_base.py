import os
import platform

import pytest

from testplan.testing.base import ProcessRunnerTest
from testplan.testing.multitest.driver.base import Driver, DriverConfig

from testplan import TestplanMock
from testplan.common.config import ConfigOption
from testplan.common.utils.testing import (
    log_propagation_disabled,
    check_report,
)

from testplan.common.utils.logger import TESTPLAN_LOGGER

from .fixtures import base


class MyDriverConfig(DriverConfig):
    @classmethod
    def get_options(cls):
        return {ConfigOption("my_val", default=""): str}


class MyDriver(Driver):
    CONFIG = MyDriverConfig

    @property
    def foobar(self):
        return "foo bar"

    @property
    def myvalue(self):
        return self.cfg.my_val


class DummyTest(ProcessRunnerTest):
    def should_run(self):
        return True

    def process_test_data(self, test_data):
        return []

    def read_test_data(self):
        pass


fixture_root = os.path.join(os.path.dirname(__file__), "fixtures", "base")


@pytest.mark.skipif(
    platform.system() == "Windows", reason="Bash files skipped on Windows."
)
@pytest.mark.parametrize(
    "binary_path, expected_report, test_kwargs",
    (
        (
            os.path.join(fixture_root, "passing", "test.sh"),
            base.passing.report.expected_report,
            {},
        ),
        (
            os.path.join(fixture_root, "passing", "test_env.sh"),
            base.passing.report.expected_report,
            dict(
                proc_env={"proc_env1": "abc", "proc_env2": "123"},
                environment=[MyDriver(name="My executable", my_val="hello")],
            ),
        ),
        (
            os.path.join(fixture_root, "sleeping", "test.sh"),
            base.sleeping.report.expected_report,
            dict(timeout="1s"),
        ),
        (
            os.path.join(fixture_root, "failing", "test.sh"),
            base.failing.report.expected_report,
            {},
        ),
        # Test fails with nonzero exit code but it is ignored
        (
            os.path.join(fixture_root, "failing", "test.sh"),
            base.passing.report.expected_report,
            dict(ignore_exit_codes=[5]),
        ),
    ),
)
def test_process_runner(binary_path, expected_report, test_kwargs):

    plan = TestplanMock(name="plan", parse_cmdline=False)

    process_test = DummyTest(name="MyTest", binary=binary_path, **test_kwargs)

    plan.add(process_test)

    with log_propagation_disabled(TESTPLAN_LOGGER):
        assert plan.run().run is True

    check_report(expected=expected_report, actual=plan.report)
