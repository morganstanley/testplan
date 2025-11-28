import os.path
import tempfile
import shutil

import pytest

import testplan.testing.multitest as mt
from testplan import defaults
from testplan.common.utils.helper import clean_runpath_if_passed
from testplan.testing import filtering, ordering
from testplan.testing.multitest.driver.app import App
from tests.helpers.pytest_test_filters import skip_on_windows

MTEST_DEFAULT_PARAMS = {
    "test_filter": filtering.Filter(),
    "test_sorter": ordering.NoopSorter(),
    "stdout_style": defaults.STDOUT_STYLE,
}


@mt.testsuite
class DummyPassing:
    @mt.testcase
    def passed(self, _, result):
        result.true(True)


@mt.testsuite
class DummyFailing:
    @mt.testcase
    def failed(self, _, result):
        result.true(False)


def _wrapped_failing_clean_runpath_if_passed(env, result):
    result.fail("deliberate fail")
    clean_runpath_if_passed(env, result)


@skip_on_windows(reason="tests doesn't run on windows")
@pytest.mark.parametrize(
    "suite, after_stop_hook, should_remove",
    [
        (DummyPassing(), clean_runpath_if_passed, True),
        (DummyFailing(), clean_runpath_if_passed, False),
        (DummyPassing(), _wrapped_failing_clean_runpath_if_passed, False),
    ],
)
def test_clean_runpath_if_passed(
    suite, after_stop_hook, should_remove, mocker
):
    with tempfile.TemporaryDirectory() as runpath:
        t = mt.MultiTest(
            name="MockMultiTest",
            runpath=runpath,
            suites=[suite],
            environment=[App("echo", binary="/bin/echo", args=["testplan"])],
            after_stop=after_stop_hook,
            **MTEST_DEFAULT_PARAMS,
        )
        try:
            t.run()
            if should_remove:
                assert os.path.exists(os.path.join(runpath, "echo")) is False
            else:
                assert os.path.exists(os.path.join(runpath, "echo")) is True
        finally:
            if t.runpath is not None:
                shutil.rmtree(t.runpath)
