#!/usr/bin/env python
# This plan contains tests that demonstrate failures as well.
"""
This example shows how to implement a custom test report exporter and
how to integrate it with your test plan.
"""
import os
import sys
from typing import Union

from testplan.report import TestReport
from testplan.testing.multitest import MultiTest, testsuite, testcase

from testplan import test_plan
from testplan.exporters.testing import Exporter
from testplan.common.utils.logger import TESTPLAN_LOGGER


@testsuite
class AlphaSuite:
    @testcase
    def test_equality_passing(self, env, result):
        result.equal(1, 1, description="passing equality")

    @testcase
    def test_equality_failing(self, env, result):
        result.equal(2, 1, description="failing equality")

    @testcase
    def test_membership_passing(self, env, result):
        result.contain(1, [1, 2, 3], description="passing membership")

    @testcase
    def test_membership_failing(self, env, result):
        result.contain(
            member=1,
            container={"foo": 1, "bar": 2},
            description="failing membership",
        )

    @testcase
    def test_regex_passing(self, env, result):
        result.regex.match(
            regexp="foo", value="foobar", description="passing regex match"
        )

    @testcase
    def test_regex_failing(self, env, result):
        result.regex.match(
            regexp="bar", value="foobaz", description="failing regex match"
        )


@testsuite
class BetaSuite:
    @testcase
    def passing_testcase_one(self, env, result):
        result.equal(1, 1, description="passing equality")

    @testcase
    def passing_testcase_two(self, env, result):
        result.equal("foo", "foo", description="another passing equality")


# To implement a basic test report exporter, just inherit from the base
# class `testplan.exporters.testing.Exporter`.


# Custom base class that will be used by the examples below
# Dumps the text content to the given file path.
class TextFileExporter(Exporter):
    def __init__(self, file_path):
        self.file_path = file_path

    def get_text_content(self, source):
        raise NotImplementedError

    def export(self, source: TestReport) -> Union[None, str]:
        with open(self.file_path, "w+") as report_file:
            report_file.write(self.get_text_content(source))
            TESTPLAN_LOGGER.user_info(
                "%s output generated at %s",
                self.__class__.__name__,
                self.file_path,
            )

        return self.file_path


class ReprExporter(TextFileExporter):
    """Dumps the native representation of the test report to a text file."""

    def get_text_content(self, source):
        return repr(source)


class IndentedTextExporter(TextFileExporter):
    """
    Iterates over flattened test data and prints out an item in each line,
    indenting by their depth on the test report tree.
    """

    def get_text_content(self, source):
        # Reports have a utility method `flatten` that gives us a list of
        # items with their depths.
        report_data = source.flatten(depths=True)

        result = []
        for depth, item in report_data:
            # Skip assertion data
            if isinstance(item, dict):
                continue

            result.append(
                "{indent}{item} - {pass_label}".format(
                    indent=depth * " ",
                    item=item,
                    pass_label="Pass" if item.passed else "Fail",
                )
            )
        return os.linesep.join(result)


curr_dir = os.path.dirname(__file__)


# To programmatically enable exporters, just pass them as a list of items
# to `exporters` argument for the `@test_plan` decorator.
@test_plan(
    name="Custom exporter example",
    exporters=[
        ReprExporter(file_path=os.path.join(curr_dir, "repr_report.txt")),
        IndentedTextExporter(
            file_path=os.path.join(curr_dir, "indented_report.txt")
        ),
    ],
)
def main(plan):

    multi_test_1 = MultiTest(name="Primary", suites=[AlphaSuite()])
    multi_test_2 = MultiTest(name="Secondary", suites=[BetaSuite()])
    plan.add(multi_test_1)
    plan.add(multi_test_2)


if __name__ == "__main__":
    sys.exit(not main())
