"""Test storing of attachments in a report."""
import re
import os

import pytest

import testplan
from testplan.testing import multitest


@multitest.testsuite
class Suite(object):

    def __init__(self, attachment_filepath):
        self._attachment_filepath = attachment_filepath

    @multitest.testcase
    def attach(self, env, result):
        result.attach(self._attachment_filepath,
                      description="attaching a file")


@pytest.fixture(scope="function")
def attachment_plan(tmpdir):
    filepath = str(tmpdir.join("attachment.txt"))
    with open(filepath, "w") as f:
        f.write("testplan\n" * 100)

    plan = testplan.Testplan(name="AttachmentPlan", parse_cmdline=False)
    plan.add(multitest.MultiTest(
            name="AttachmentTest",
            suites=[Suite(filepath)]))
    return plan


def test_attach(attachment_plan):
    """Test running a Testplan that stores a single attachment."""
    plan = attachment_plan
    plan_result = plan.run()
    assert plan_result  # Plan should pass.

    report = plan_result.report
    attachments = report.attachments
    testcase_report = report.entries[0].entries[0].entries[0]
    assert testcase_report.name == "attach"
    assert len(testcase_report.entries) == 1

    attachment_entry = testcase_report.entries[0]
    assert len(attachments) == 1
    dst_path = list(attachments.keys())[0]

    # Expect the attachment to be stored as "attachment-[HASH]-[FILESIZE].txt"
    assert re.match(r"attachment-[0-9a-f]+-[0-9]+.txt", dst_path)
    assert attachments[dst_path] == attachment_entry["source_path"]
