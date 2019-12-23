#!/usr/bin/env python
# This plan contains tests that demonstrate failures as well.
"""
This example shows:

* How to generate multiple PDF reports by tag using tags.

* How to configure the generated PDF report styles
  programmatically and via command line.
"""
import os
import sys

from testplan.testing.multitest import MultiTest, testsuite, testcase

from testplan import test_plan
from testplan.report.testing.styles import Style


@testsuite(tags='server')
class AlphaSuite(object):

    @testcase(tags={'color': 'red'})
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

    @testcase(tags={'color': 'blue'})
    def test_regex_passing(self, env, result):
        result.regex.match(
            regexp='foo',
            value='foobar',
            description='passing regex match')

    @testcase(tags={'color': ('red', 'blue')})
    def test_regex_failing(self, env, result):
        result.regex.match(
            regexp='bar',
            value='foobaz',
            description='failing regex match')


@testsuite(tags='client')
class BetaSuite(object):

    @testcase
    def passing_testcase_one(self, env, result):
        result.equal(1, 1, description='passing equality')

    @testcase(tags={'color': 'red'})
    def passing_testcase_two(self, env, result):
        result.equal('foo', 'foo', description='another passing equality')


# `@test_plan` accepts shortcut arguments `report_tags` and `report_tags_all`
# for Tag filtered PDF reports, meaning that you don't have to instantiate a
# TagFilteredPDFExporter explicitly.

# You can use `pdf_style` argument to apply common styling to all
# generated PDF reports.

# If you want to test out command line configuration for PDF generation please
# remove `report_tags`, `report_tags_all`, `report_dir` and `pdf_style`
# arguments from below as programmatic declaration overrides
# command line arguments.

# An example command line call for tag filtered PDFs would be:
# ./test_plan --report-dir . --report-tags server color=red,blue
# --report-tags client color=red,blue --report-tags-all color=red,blue

# The command above will generate 3 PDFs, assuming
# the filtered test data is not empty.

@test_plan(
    name='Basic PDF Report Example',
    # Each item in the list corresponds to a PDF report
    report_tags=[
        'server',  # Report contains tests tagged with `server`
        'client',  # Report contains tests tagged with `client`
        # Report contains tests tagged with `color=red` OR `color=blue`
        {'color': ('red', 'blue')}
    ],
    # Each item in the list corresponds to a PDF report
    report_tags_all=[
        # Report contains tests tagged with `server` AND `color=red`
        {'simple': 'server', 'color': 'red'},
        # Report contains tests tagged with `color=red` AND `color=blue`
        {'color': ('red', 'blue')}
    ],
    # All of the PDFs are going to be generated in this directory.
    report_dir=os.path.dirname(__file__),
    # This will be the common styling for all PDFs.
    pdf_style=Style(passing='testcase', failing='assertion-detail')
)
def main(plan):

    multi_test_1 = MultiTest(name='Primary', suites=[AlphaSuite()])
    multi_test_2 = MultiTest(name='Secondary', suites=[BetaSuite()])
    plan.add(multi_test_1)
    plan.add(multi_test_2)


if __name__ == '__main__':
    sys.exit(not main())
