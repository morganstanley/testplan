import os
import re
import sys

import psutil
import pytest

import testplan.testing.multitest as mt
from testplan.base import TestplanMock as Mockplan
from testplan.testing.multitest.driver.app import App
from tests.unit.testplan.testing.multitest.driver.myapp.test_app import (
    MYAPP_DIR,
)


@mt.testsuite
class GoodSuite:
    @mt.testcase
    def passed(self, env, result):
        result.true(True)


@mt.testsuite
class BadSuite:
    @mt.testcase
    def illegal(self, env, result):
        env.app.proc.terminate()
        result.false(True)


def make_mt(app_args, driver_args):
    def _():
        return App(
            name="App",
            binary=sys.executable,
            args=[
                "-u",
                os.path.join(MYAPP_DIR, "multi_proc_app.py"),
                *app_args,
            ],
            stdout_regexps=[
                re.compile(r"^curr pid (?P<pid>[0-9]+)$"),
                re.compile(r"^child 1 pid (?P<pid1>[0-9]+)$"),
                re.compile(r"^child 2 pid (?P<pid2>[0-9]+)$"),
            ],
            **driver_args,
        )

    yield mt.MultiTest("mt1", [GoodSuite()], environment=[_()])
    yield mt.MultiTest("mt2", [BadSuite()], environment=[_()])


@pytest.mark.parametrize(
    "app_args, driver_args, has_exception",
    (
        (["--mask-sigterm", "parent", "--sleep-time", "1"], {}, False),
        (
            ["--mask-sigterm", "parent", "--sleep-time", "5"],
            {"sigint_timeout": 1},
            True,
        ),
        (
            ["--mask-sigterm", "parent", "--sleep-time", "5"],
            {"sigterm_timeout": 1},
            True,
        ),
    ),
)
def test_bad_app(app_args, driver_args, has_exception):
    mockplan = Mockplan(
        name="bad_app_mock_test",
    )
    for mt in make_mt(app_args, driver_args):
        mockplan.add(mt)
    report = mockplan.run().report

    curr_proc = psutil.Process()
    child_procs = curr_proc.children(recursive=True)
    assert len(child_procs) == 0

    if has_exception:
        for e in map(lambda x: x.entries[2].entries[0], report.entries):
            assert e.logs
            assert "TimeoutException" in e.logs[0]["message"]
