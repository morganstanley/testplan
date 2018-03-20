# This plan contains tests that demonstrate failures as well.
"""
This example shows:

* How to generate a PDF report of test results.

* How to configure the PDF report style programmatically and via command line.

"""
import os
import sys

from testplan.testing.multitest import MultiTest, testsuite, testcase

from testplan import test_plan
from testplan.report.testing.styles import Style


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


# `@test_plan` accepts shortcut arguments `pdf_path` and `pdf_style`
# for PDF reports, meaning that you don't have to instantiate a PDFExporter
# explicitly for basic PDF report generation.

# A PDF report can also be generated via command line arguments like:
# ./test_plan.py --pdf <report-path> --pdf-style <report-style>

# <report-path> should be valid system file path and <report-style> should be
# one of: `result-only`, `summary`, `extended-summary`, `detailed`.

# If you want to test out command line configuration for PDF generation please
# remove `pdf_path` and `pdf_style` arguments from below as
# programmatic declaration overrides command line arguments.

@test_plan(
    name='Basic PDF Report Example',
    pdf_path=os.path.join(os.path.dirname(__file__), 'report.pdf'),
    pdf_style=Style(passing='case', failing='assertion-detail'),
)
def main(plan):

    multi_test_1 = MultiTest(name='Primary', suites=[AlphaSuite()])
    multi_test_2 = MultiTest(name='Secondary', suites=[BetaSuite()])
    plan.add(multi_test_1)
    plan.add(multi_test_2)


if __name__ == '__main__':
    sys.exit(not main())
