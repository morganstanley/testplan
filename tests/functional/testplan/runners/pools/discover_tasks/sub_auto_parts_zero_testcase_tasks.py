from testplan.runners.pools.tasks.base import task_target
from testplan.testing.multitest import MultiTest, testsuite, testcase
from testplan.testing.multitest.driver import Driver


@testsuite
class Suite1:
    """A test suite with no testcases."""

    pass


@task_target(multitest_parts="auto")
def make_auto_part_multitest1():
    return MultiTest(
        name="Proj1-suite",
        suites=[Suite1()],
        environment=[Driver("Noop")],
    )
