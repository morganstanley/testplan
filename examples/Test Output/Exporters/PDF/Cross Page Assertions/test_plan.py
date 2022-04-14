#!/usr/bin/env python
# This plan contains tests that demonstrate failures as well.
"""
This example generates a sample pdf that contains assertions that could cross
multiple pages.
"""
import os
import sys

from testplan.testing.multitest import MultiTest, testsuite, testcase

from testplan import test_plan
from testplan.report.testing.styles import Style


@testsuite
class AlphaSuite:

    msg = (
        "This is a super looooooooooog message with indents, extra spaces\n"
        "    and <Test>special</Test> characters,\n"
        "    and    it    will    be    written    as-is    in    pdf.\n" * 40
    )

    @testcase
    def test_log_assertions(self, env, result):
        result.log(self.msg, description="Logging a long msg")

    @testcase
    def test_regex_assertions(self, env, result):

        result.regex.match(
            regexp=".*super",
            value=self.msg,
            description="Single line match expect to pass",
        )
        result.regex.multiline_match(
            regexp=".*super",
            value=self.msg,
            description="Multiline match expect to pass",
        )
        result.regex.not_match(
            regexp=".*super",
            value=self.msg,
            description="Not_match expect to fail",
        )
        result.regex.search(
            regexp="super",
            value=self.msg,
            description="Search - highlights the first occurrence",
        )
        result.regex.findall(
            regexp="super",
            value=self.msg,
            description="Findall - highlights all occurrences",
        )
        result.regex.matchline(
            regexp=".*super", value=self.msg, description="Line-by-line match"
        )


# `@test_plan` accepts shortcut arguments `pdf_path` and `pdf_style`
# for PDF reports, meaning that you don't have to instantiate a PDFExporter
# explicitly for basic PDF report generation.

# A PDF report can also be generated via command line arguments like:
# ./test_plan.py --pdf <report-path> --pdf-style <report-style>

# <report-path> should be valid system file path and <report-style> should be
# one of: `result-only`, `summary`, `extended-summary`, `detailed`.

# If you want to test out command line configuration for PDF generation
# please directly use --pdf argument because command line arguments can
# override programmatic declaration.


@test_plan(
    name="Basic PDF Report Example",
    pdf_path=os.path.join(os.path.dirname(__file__), "report.pdf"),
    pdf_style=Style(passing="assertion-detail", failing="assertion-detail"),
)
def main(plan):

    plan.add(MultiTest(name="Primary", suites=[AlphaSuite()]))


if __name__ == "__main__":
    sys.exit(not main())
