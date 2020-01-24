#!/usr/bin/env python
"""
    This example shows how to implement a custom lister for
    displaying test context of a test plan.
"""
import sys

from testplan.testing.multitest import MultiTest, testsuite, testcase

from testplan import test_plan
from testplan.testing.listing import BaseLister


@testsuite
class Alpha(object):
    @testcase
    def test_a(self, env, result):
        pass

    @testcase(tags="server")
    def test_b(self, env, result):
        pass

    @testcase(tags={"color": "blue"})
    def test_c(self, env, result):
        pass


@testsuite(tags="server")
class Beta(object):
    @testcase(tags="client")
    def test_a(self, env, result):
        pass

    @testcase(tags={"color": "red"})
    def test_b(self, env, result):
        pass

    @testcase(tags={"color": ("blue", "yellow")})
    def test_c(self, env, result):
        pass


@testsuite(tags="client")
class Gamma(object):
    @testcase
    def test_a(self, env, result):
        pass

    @testcase(tags={"color": ("yellow", "red")})
    def test_b(self, env, result):
        pass

    @testcase(parameters=list(range(100)))
    def test_c(self, env, result, val):
        pass


# To implement a custom lister, we need to inherit from `listing.BaseLister`
# override `get_output` method and return a string representation of
# the current test instance (e.g. multitest) and possibly its test
#  context, like suites & testcases


class ExampleLister(BaseLister):
    """
        Displays test instances and their suites (if available)
        along with number of testcases per suite in a single line.

        e.g.

            Multitest A: Foo (3 testcases), Bar (2 testcases)
            Multitest B: Baz (3 testcases)
    """

    def get_output(self, instance):
        if isinstance(instance, MultiTest):
            test_context = instance.test_context
            if test_context:
                suite_data = ", ".join(
                    [
                        "{suite_name} ({num_testcases} testcases)".format(
                            suite_name=suite.__class__.__name__,
                            num_testcases=len(testcases),
                        )
                        for suite, testcases in test_context
                    ]
                )
                return "{instance_name}: {suite_data}".format(
                    instance_name=instance.name, suite_data=suite_data
                )
        else:
            # Coming soon in future releases
            raise NotImplementedError


# Running this plan will print out the test information using the
# custom test lister we defined above.
@test_plan(name="Custom test lister example", test_lister=ExampleLister())
def main(plan):

    test1 = MultiTest(name="Primary", suites=[Alpha(), Beta()])
    test2 = MultiTest(name="Secondary", suites=[Gamma()])
    plan.add(test1)
    plan.add(test2)


if __name__ == "__main__":
    sys.exit(not main())
