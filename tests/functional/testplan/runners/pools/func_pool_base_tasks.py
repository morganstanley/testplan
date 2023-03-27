"""Base Testplan Tasks shared by different functional tests."""

import os
import tempfile
from pathlib import Path

from testplan.common.utils.strings import slugify
from testplan.testing.multitest import MultiTest, testcase, testsuite
from testplan.testing.multitest.base import MultiTestConfig


@testsuite
class MyImportedSuite:
    @testcase
    def test_comparison(self, env, result):
        # Lambda won't be serialized by pickle.
        my_lambda = lambda x: x
        result.equal(1, my_lambda(1), "equality description")
        result.log(env.parent.runpath)
        assert isinstance(env.parent.cfg, MultiTestConfig)
        assert os.path.exists(env.parent.runpath) is True
        assert env.parent.runpath.endswith(slugify(env.parent.cfg.name))

    @testcase
    def test_attach(self, env, result):
        with tempfile.NamedTemporaryFile(
            mode="w", suffix=".txt", delete=False
        ) as tmpfile:
            tmpfile.write("testplan\n")

        result.attach(tmpfile.name, description=os.path.basename(tmpfile.name))
        os.remove(tmpfile.name)


def get_imported_mtest(name):
    """TODO."""
    return MultiTest(name="MTest{}".format(name), suites=[MyImportedSuite()])


@testsuite
class SuiteKillingWorker:
    def __init__(self, boobytrap_path: str):
        self._boobytrap_path = Path(boobytrap_path)

    @testcase
    def test_comparison(self, env, result):
        if self._boobytrap_path.exists():
            self._boobytrap_path.unlink()
            print("Killing worker {}".format(os.getpid()))
            os.kill(os.getpid(), 9)
        result.equal(1, 1, "equality description")
        result.log(env.parent.runpath)
        assert isinstance(env.parent.cfg, MultiTestConfig)
        assert os.path.exists(env.parent.runpath) is True
        assert env.parent.runpath.endswith(slugify(env.parent.cfg.name))


def multitest_kill_one_worker(boobytrap: str):
    """Test that kills one worker."""
    return MultiTest(
        name="MTestKiller", suites=[SuiteKillingWorker(boobytrap)]
    )


@testsuite
class SimpleSuite:
    @testcase
    def test_simple(self, env, result):
        pass


def multitest_kill_workers(parent_pid):
    """To kill all child workers."""
    if os.getpid() != parent_pid:  # Main process should not be killed
        os.kill(os.getpid(), 9)
    else:
        return MultiTest(name="MTestKiller", suites=[SimpleSuite()])


@testsuite
class SuiteKillRemoteWorker:
    @testcase
    def kill_remote_worker(self, env, result):
        os.kill(os.getpid(), 9)


def multitest_kill_remote_workers():
    return MultiTest(
        name="MTestKillRemoteWorker", suites=[SuiteKillRemoteWorker()]
    )


def target_raises_in_worker(parent_pid):
    """
    Task target that raises when being materialized in process/remote worker.
    """
    if os.getpid() != parent_pid:
        raise RuntimeError("Materialization failed in worker")

    return MultiTest(name="MTest", suites=[MyImportedSuite()])
