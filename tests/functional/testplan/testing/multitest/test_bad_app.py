from pytest_test_filters import skip_module_on_windows

skip_module_on_windows(reason='No need to dive into Windows "signals".')


import os
import re
import signal
import sys
from datetime import datetime
from itertools import count

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


def make_app(app_args, driver_args, name="app"):
    return App(
        name=name,
        binary=sys.executable,
        args=[
            "-u",
            os.path.join(MYAPP_DIR, "multi_proc_app.py"),
            *app_args,
        ],
        stdout_regexps=[
            re.compile(r"^parent pid (?P<pid>[0-9]+)$"),
            re.compile(r"^child 1 pid (?P<pid1>[0-9]+)$"),
            re.compile(r"^child 2 pid (?P<pid2>[0-9]+)$"),
        ],
        **driver_args,
    )


@pytest.mark.parametrize(
    "app_args, driver_args, suite_cls",
    (
        # normal operation
        ([], {}, GoodSuite),
        # illegal operation would cause plan crash
        ([], {}, BadSuite),
        # terms all child, parent exit normally though sigterm trapped
        (["--mask-sigterm", "parent"], {}, GoodSuite),
        # parent term timeout, parent killed
        (
            ["--mask-sigterm", "parent", "--sleep-time", "5"],
            {"sigint_timeout": 1},
            GoodSuite,
        ),
        # parent killed with child orphaned, exc suppressed
        (
            ["--mask-sigterm", "parent", "--sleep-time", "5"],
            {"stop_timeout": 1, "stop_signal": signal.SIGKILL},
            GoodSuite,
        ),
    ),
    ids=count(0),
)
def test_basic_loose(app_args, driver_args, suite_cls, mocker):
    mock_warn = mocker.patch("warnings.warn")
    mockplan = Mockplan(
        name="bad_app_mock_test",
    )
    mockplan.add(
        mt.MultiTest(
            "dummy_mt",
            suite_cls(),
            environment=[make_app(app_args, driver_args)],
        )
    )
    report = mockplan.run().report

    if "sigint_timeout" in driver_args:
        mock_warn.assert_called_once()
        assert re.search(
            r"sigint_timeout.*deprecated", mock_warn.call_args[0][0]
        )

    # force_stop triggered, direct child terminated
    curr_proc = psutil.Process()
    child_procs = curr_proc.children(recursive=True)
    assert len(child_procs) == 0

    assert report.status != report.status.ERROR


@pytest.mark.parametrize(
    "app_args, driver_args, dependencies, stopped_order",
    (
        (
            ["--mask-sigterm", "parent", "--sleep-time", "1"],
            {},
            {"app2": "app"},
            ["app3", "app", "app2"],
        ),
        (
            ["--mask-sigterm", "all"],
            {"stop_timeout": 1},
            {"app2": "app"},
            ["app3", "app", "app2"],
        ),
    ),
    ids=count(0),
)
def test_complex(app_args, driver_args, dependencies, stopped_order):
    mockplan = Mockplan(
        name="bad_app_mock_test",
        driver_info=True,
    )
    app = make_app(app_args, driver_args)
    app2 = make_app([], {}, name="app2")
    app3 = make_app([], {}, name="app3")
    dmap = {app.name: app, app2.name: app2}
    dep = (
        dependencies
        and {dmap[k]: dmap[v] for k, v in dependencies.items()}
        or None
    )
    mockplan.add(
        mt.MultiTest(
            "dummy_mt",
            GoodSuite(),
            environment=[app, app2, app3],
            dependencies=dep,
        )
    )
    report = mockplan.run().report

    # here we use data in TableLog entry to check the order of stopping
    stopping_table = (
        report.entries[0].entries[2].entries[0].entries[0]["table"]
    )
    assert (
        list(
            map(
                lambda r: r[1],
                sorted(
                    filter(lambda x: x[3], stopping_table),
                    key=lambda x: datetime.strptime(x[3], "%H:%M:%S.%f"),
                ),
            )
        )
        == stopped_order
    )
