"""Example test suite to demonstrate grouped parallel MultiTest execution."""
import time

from testplan.testing.multitest import MultiTest
from testplan.testing.multitest.suite import testsuite, testcase
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
        self._test_g2_1_done = False

    @testcase(execution_group='first')
    def test_g1_1(self, env, result):
        """Wait for test_g1_2 to also acquire the first resource."""
        with env.resources['first'] as res:
            result.true(res.active)
            while res.refcount < 2:
                result.log('Waiting for test_g1_2...')
                time.sleep(1)

    @testcase(execution_group='second')
    def test_g2_1(self, env, result):
        """Assert that no other test holds the second resource."""
        with env.resources['second'] as res:
            result.true(res.active)
            result.equal(res.refcount, 1)
        self._test_g2_1_done = True

    @testcase(execution_group='first')
    def test_g1_2(self, env, result):
        """
        Sleep before acquiring the first resource. Wait for test_g1_1 to
        release it first.
        """
        time.sleep(2.5)

        with env.resources['first'] as res:
            result.true(res.active)
            result.equal(res.refcount, 2)
            while res.refcount == 2:
                result.log('Waiting for test_g1_1...')
                time.sleep(1)

    @testcase(execution_group='second')
    def test_g2_2(self, env, result):
        """Wait for test_g2_1 to release the resource before acquiring it."""
        while not self._test_g2_1_done:
            result.log('Waiting for test_g2_1 to finish...')
            time.sleep(1)

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
