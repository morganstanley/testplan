#!/usr/bin/env python
"""
    This example shows how to implement a custom lister for
    displaying test context of a test plan.
"""
import sys

from testplan.testing.multitest import MultiTest, testsuite, testcase

from testplan import test_plan
from testplan.testing.listing import BaseLister, listing_registry


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
#  context, like suites & testcases.
#
# To use in the commandline add NAME and DESCRIPTION and register with
# listing_registry


class HelloWorldLister(BaseLister):
    """
    Displays 'Hello World" for each MultiTest

    e.g.

        Hello World: Primary
        Hello World: Secondary
    """

    NAME = "HELLO_WORLD"
    DESCRIPTION = "This lister print Hello World for each multitest"

    def get_output(self, instance):
        return "Hello World: {}".format(instance.name)


listing_registry.add_lister(HelloWorldLister())


# use --info hello-world to see the action
#
# it is also there in the --help text
#
#   --info TEST_INFO      (default: None)
#                         "pattern" - List tests in `--patterns` / `--tags` compatible format.
#                                 Max 25 testcases per suite will be displayed
#                         "name" - List tests in readable format.
#                                 Max 25 testcases per suite will be displayed
#                         "pattern-full" - List tests in `--patterns` / `--tags` compatible format.
#                         "name-full" - List tests in readable format.
#                         "count" - Lists top level instances and total number of suites & testcases per instance.
#                         "hello-world" - This lister print Hello World for each multitest
@test_plan(name="Custom test lister example")
def main(plan):
    test1 = MultiTest(name="Primary", suites=[Alpha(), Beta()])
    test2 = MultiTest(name="Secondary", suites=[Gamma()])
    plan.add(test1)
    plan.add(test2)


if __name__ == "__main__":
    sys.exit(not main())
