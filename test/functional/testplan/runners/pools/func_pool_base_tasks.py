"""TODO."""

import os

import psutil
from testplan.testing.multitest import MultiTest, testsuite, testcase
from testplan.testing.multitest.base import MultiTestConfig


@testsuite
class MySuite(object):

    @testcase
    def test_comparison(self, env, result):
        result.equal(1, 1, 'equality description')
        result.log(env.runpath)
        assert isinstance(env.cfg, MultiTestConfig)
        assert os.path.exists(env.runpath) is True
        assert env.runpath.endswith(env.cfg.name)


def get_mtest(name):
    """TODO."""
    return MultiTest(name='MTest{}'.format(name), suites=[MySuite()])


def get_mtest_imported(name):
    """TODO."""
    return MultiTest(name='MTest{}'.format(name), suites=[MySuite()])


@testsuite
class MySuite(object):

    @testcase
    def test_comparison(self, env, result):
        result.equal(1, 1, 'equality description')
        result.log(env.runpath)
        assert isinstance(env.cfg, MultiTestConfig)
        assert os.path.exists(env.runpath) is True
        assert env.runpath.endswith(env.cfg.name)

@testsuite
class SuiteKillingWorker(object):

    @testcase
    def test_comparison(self, env, result):
        result.equal(1, 1, 'equality description')
        result.log(env.runpath)
        assert isinstance(env.cfg, MultiTestConfig)
        assert os.path.exists(env.runpath) is True
        assert env.runpath.endswith(env.cfg.name)


def multitest_kill_one_worker(name, parent_pid, size):
    """Test that kills one worker."""
    parent = psutil.Process(parent_pid)
    if len(parent.children(recursive=True)) == size:
        print('Killing worker {}'.format(os.getpid()))
        os.kill(os.getpid(), 9)
    return MultiTest(name='MTest{}'.format(name),
                     suites=[SuiteKillingWorker()])


def multitest_kills_worker():
    """To kill all child workers."""
    os.kill(os.getpid(), 9)

