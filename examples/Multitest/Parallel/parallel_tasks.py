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

    NOTE: when running a parallel MultiTest, all testcases from a given
    execution group are run together, regardless of the order they are defined
    within the testsuite class. Each execution group is run separately from all
    others. This is in contrast to the default serial mode, where testcases
    are run serially in the order they are defined within the testsuite class.
    """

    def __init__(self):
        # A Barrier is a synchronisation primitive which allows a fixed number
        # of threads (in our case, 2) to wait for each other. We use it here
        # to demonstrate that testcases are run concurrently and how they may
        # be synchronised with each other.
        #
        # Note that on Python 3 you can use the Barrier class from the standard
        # library:
        # https://docs.python.org/3.7/library/threading.html#barrier-objects .
        # Here we use a backported Barrier provided by Testplan, which works
        # on both Python 2 and 3.
        self._barrier = thread_utils.Barrier(2)

        # The Event synchronisation primitive allows one thread to signal to
        # another that is waiting on the first thread to do some work. We use
        # it here to demonstrate another way testcases within the same
        # execution group may be synchronised with each other.
        self._test_g2_1_done = threading.Event()

    @testcase(execution_group='first')
    def test_g1_1(self, env, result):
        """
        Wait for test_g1_2 to also acquire the first resource. Assert that the
        refcount is 2.
        """
        self._test_g1_impl(env, result)

    @testcase(execution_group='second')
    def test_g2_1(self, env, result):
        """Assert that no other test holds the second resource."""
        with env.resources['second'] as res:
            result.true(res.active)
            result.equal(res.refcount, 1)
        self._test_g2_1_done.set()

    @testcase(execution_group='first')
    def test_g1_2(self, env, result):
        """
        Mirror image of test_g1_1. We wait for test_g1_1 to acquire the first
        resource while running in another thread, then assert that the refcount
        is 2.
        """
        self._test_g1_impl(env, result)

    @testcase(execution_group='second')
    def test_g2_2(self, env, result):
        """Wait for test_g2_1 to release the resource before acquiring it."""
        self._test_g2_1_done.wait()

        with env.resources['second'] as res:
            result.true(res.active)
            result.equal(res.refcount, 1)

    def _test_g1_impl(self, env, result):
        """
        Implementation of test_g1 testcases. Both testcases use the same logic
        but are run concurrently in separate threads.
        """
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
