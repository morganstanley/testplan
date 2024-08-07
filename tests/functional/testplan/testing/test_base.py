import os

import pytest

from testplan.testing.base import ProcessRunnerTest
from testplan.testing.multitest.driver.base import Driver, DriverConfig

from testplan.common.config import ConfigOption
from testplan.common.utils.testing import check_report

from .fixtures import base

from pytest_test_filters import skip_on_windows


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


@skip_on_windows(reason="Bash files skipped on Windows.")
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
            base.passing.report.expected_report_with_driver,
            dict(
                proc_env={
                    "proc_env1": "abc",
                    "proc_env2": "123",
                    "test_name": "{{name}}",
                },
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
def test_process_runner(mockplan, binary_path, expected_report, test_kwargs):

    process_test = DummyTest(name="MyTest", binary=binary_path, **test_kwargs)
    mockplan.add(process_test)
    assert mockplan.run().run is True

    check_report(expected=expected_report, actual=mockplan.report)
