import time

from testplan.testing.multitest import MultiTest, testsuite, testcase

@testsuite
class Suite1(object):
    """A test suite which will be executed locally."""
    @testcase(
        parameters=(2, 1, 0)
    )
    def test_true(self, env, result, val):
        result.true(val, description='Check if value is true')


@testsuite
class Suite2(object):
    """A test suite which will be executed locally (timeout)."""
    @testcase
    def test_false(self, env, result):
        result.false(None, description='Check if value is false')
        time.sleep(600)


@testsuite
class Suite3(object):
    """A test suite which will be executed in thread pool."""
    @testcase(
        parameters=(
            (1+2, 3),
            (1*2, 2),
            (1%2, 1)
        )
    )
    def test_equal(self, env, result, a, b):
        result.equal(a, b, description='Check if 2 values are equal')


@testsuite
class Suite4(object):
    """A test suite which will be executed in thread pool (timeout)."""
    @testcase
    def test_not_equal(self, env, result):
        result.not_equal(1, 0, description='Check if 2 values are not equal')
        time.sleep(600)


@testsuite
class Suite5(object):
    """A test suite which will be executed in process pool."""
    @testcase(
        parameters=(
            ('foo', ['foo', 'bar', 'baz']),
            ('bar', ['foo', 'bar', 'baz']),
            ('baz', ['foo', 'bar', 'baz'])
        )
    )
    def test_contain(self, env, result, item, arr):
        result.contain(item, arr, description='Check if an item is in a list')
        if item == 'baz':
            raise Exception('Raise exception deliberately')


@testsuite
class Suite6(object):
    """A test suite which will be executed in process pool (timeout)."""
    @testcase
    def test_not_contain(self, env, result):
        result.not_contain('foobar', ['foo', 'bar', 'baz'],
                           description='Check if an item is not in a list')
        time.sleep(600)


def get_mtest1():
    return MultiTest(name='MTest1', suites=[Suite1()])


def get_mtest2():
    return MultiTest(name='MTest2', suites=[Suite2()])


def get_mtest3():
    return MultiTest(name='MTest3', suites=[Suite3()])


def get_mtest4():
    return MultiTest(name='MTest4', suites=[Suite4()])


def get_mtest5():
    return MultiTest(name='MTest5', suites=[Suite5()])


def get_mtest6():
    return MultiTest(name='MTest6', suites=[Suite6()])
