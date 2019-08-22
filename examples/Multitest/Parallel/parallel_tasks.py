"""Example test suite to demonstrate grouped parallel MultiTest execution."""
import threading

from testplan.testing.multitest import MultiTest
from testplan.testing.multitest.suite import testsuite, testcase
from testplan.common.utils import thread as thread_utils

import resource_manager


@testsuite
class SampleTest(object):
    """
    Example test suite. The test cases are split into two different execution
    groups. Only tests from the same group will be executed in parallel with
    each other - the groups overall are executed serially. To demonstrate
    this, each test acquires one of two resources that cannot both be acquired
    in parallel.

    You will find that modifying a single test from the "first" group to acquire
    the "second" resource (or vice-versa) will cause the test to fail.
    """

    def __init__(self):
        self._test_g2_1_done = threading.Event()
        self._barrier = thread_utils.Barrier(2)

    @testcase(execution_group='first')
    def test_g1_1(self, env, result):
        """
        Wait for test_g1_2 to also acquire the first resource. Assert that the
        refcount is 2.
        """
        self._test_g1_impl(env, result)

    @testcase(execution_group='first')
    def test_g1_2(self, env, result):
        """
        Mirror image of test_g1_1. We wait for test_g1_1 to acquire the first
        resource while running in another thread, then assert that the refcount
        is 2.
        """
        self._test_g1_impl(env, result)

    def _test_g1_impl(self, env, result):
        with env.resources['first'] as res:
            result.true(res.active)

            # Wait for both threads to acquire the resource.
            self._barrier.wait()

            # Both threads have acquired the resource - check that the refcount
            # is 2.
            result.equal(res.refcount, 2)

            # Wait for both threads to check the refcount before releasing the
            # resource.
            self._barrier.wait()

    @testcase(execution_group='second')
    def test_g2_1(self, env, result):
        """Assert that no other test holds the second resource."""
        with env.resources['second'] as res:
            result.true(res.active)
            result.equal(res.refcount, 1)
        self._test_g2_1_done.set()

    @testcase(execution_group='second')
    def test_g2_2(self, env, result):
        """Wait for test_g2_1 to release the resource before acquiring it."""
        self._test_g2_1_done.wait()

        with env.resources['second'] as res:
            result.true(res.active)
            result.equal(res.refcount, 1)


def make_multitest():
    """
    Callable target to build a MultiTest. The `thread_pool_size` argument
    instructs Testplan to create a thread pool for running the MultiTest
    testcases.
    """
    return MultiTest(
        name='Testcase Parallezation',
        suites=[SampleTest()],
        thread_pool_size=2,
        environment=[
            resource_manager.ExclusiveResourceManager(name='resources')])
