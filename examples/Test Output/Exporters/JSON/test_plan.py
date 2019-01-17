#!/usr/bin/env python
# This plan contains tests that demonstrate failures as well.
"""
This example shows how to generate a JSON report of test results.
"""
import os
import sys

from testplan.testing.multitest import MultiTest, testsuite, testcase

from testplan import test_plan


@testsuite
class AlphaSuite(object):

    @testcase
    def test_equality_passing(self, env, result):
        result.equal(1, 1, description='passing equality')

    @testcase
    def test_equality_failing(self, env, result):
        result.equal(2, 1, description='failing equality')

    @testcase
    def test_membership_passing(self, env, result):
        result.contain(1, [1, 2, 3], description='passing membership')

    @testcase
    def test_membership_failing(self, env, result):
        result.contain(
            member=1,
            container={'foo': 1, 'bar': 2},
            description='failing membership')

    @testcase
    def test_regex_passing(self, env, result):
        result.regex.match(
            regexp='foo',
            value='foobar',
            description='passing regex match')

    @testcase
    def test_regex_failing(self, env, result):
        result.regex.match(
            regexp='bar',
            value='foobaz',
            description='failing regex match')


@testsuite
class BetaSuite(object):

    @testcase
    def passing_testcase_one(self, env, result):
        result.equal(1, 1, description='passing equality')

    @testcase
    def passing_testcase_two(self, env, result):
        result.equal('foo', 'foo', description='another passing equality')


# `@test_plan` accepts shortcut argument `json_path`
# for JSON reports, meaning that you don't have to instantiate a JSONExporter
# explicitly for basic JSON report generation.

# A JSON report can also be generated via command line arguments like:
# ./test_plan.py --json <report-path>

# <report-path> should be valid system file path.

# If you want to test out command line configuration for JSON generation please
# remove `json_path` arguments from below as
# programmatic declaration overrides command line arguments.

# After running this example, you can see how a JSON can be converted back
# into a report object via `json_to_pdf.py` script.

@test_plan(
    name='Basic JSON Report Example',
    json_path=os.path.join(os.path.dirname(__file__), 'report.json'),
)
def main(plan):

    multi_test_1 = MultiTest(name='Primary', suites=[AlphaSuite()])
    multi_test_2 = MultiTest(name='Secondary', suites=[BetaSuite()])
    plan.add(multi_test_1)
    plan.add(multi_test_2)


if __name__ == '__main__':
    sys.exit(not main())
