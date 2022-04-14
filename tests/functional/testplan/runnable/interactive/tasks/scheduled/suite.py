from testplan.testing.multitest import MultiTest
from testplan.testing.multitest.suite import testsuite, testcase
from .foo import mod


@testsuite
class Suite(object):
    @testcase
    def case(self, env, result):
        result.equal(1, mod.VALUE, description="Equal Assertion")


class TaskManager(object):
    @staticmethod
    def make_mtest(name):
        return MultiTest(name=name, suites=[Suite()])
