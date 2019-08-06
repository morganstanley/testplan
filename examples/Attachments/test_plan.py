#!/usr/bin/env python
"""Demonsrates attaching files to the Testplan report."""
import tempfile
import sys

import testplan
from testplan.testing import multitest


@multitest.testsuite
class TestSuite(object):
    """Example test suite."""

    @multitest.testcase
    def test_attach(self, env, result):
        """Attaches a file to the report."""
        with tempfile.NamedTemporaryFile(
                mode="w", suffix=".txt", delete=False) as tmpfile:
            tmpfile.write("testplan\n" * 100)

        result.attach(tmpfile.name, description="Attaching a text file")


@testplan.test_plan(name="AttachmentPlan")
def main(plan):
    """Define a Testplan with a single MultiTest."""
    plan.add(multitest.MultiTest(
        name="TestAttachments",
        suites=[TestSuite()]))


if __name__ == "__main__":
    res = main()
    sys.exit(res.exit_code)

