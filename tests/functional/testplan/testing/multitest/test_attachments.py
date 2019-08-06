"""Test storing of attachments in a report."""
import re
import os

import pytest

import testplan
from testplan.testing import multitest


@multitest.testsuite
class Suite1(object):

    def __init__(self, attachment_filepath):
        self._attachment_filepath = attachment_filepath

    @multitest.testcase
    def attach(self, env, result):
        result.attach(self._attachment_filepath,
                      description="attaching a file")


@multitest.testsuite
class Suite2(object):

    def __init__(self, attachment_filepath):
        self._attachment_filepath = attachment_filepath

    @multitest.testcase
    def attach(self, env, result):
        result.attach(self._attachment_filepath,
                      description="attaching a file")


@pytest.fixture(scope="function")
def attachment_path(tmpdir):
    filepath = str(tmpdir.join("attachment.txt"))
    with open(filepath, "w") as f:
        f.write("testplan\n" * 100)
    return filepath


@pytest.fixture(scope="function")
def attachment_plan(attachment_path):
    plan = testplan.Testplan(name="AttachmentPlan", parse_cmdline=False)
    plan.add(multitest.MultiTest(
            name="AttachmentTest",
            suites=[Suite1(attachment_path)]))
    return plan


@pytest.fixture(scope="function")
def multi_attachment_plan(attachment_path):
    plan = testplan.Testplan(name="AttachmentPlan", parse_cmdline=False)
    plan.add(multitest.MultiTest(
            name="AttachmentTest",
            suites=[Suite1(attachment_path), Suite2(attachment_path)]))
    return plan


def test_attach(attachment_plan):
    """Test running a Testplan that stores a single attachment."""
    plan_result = attachment_plan.run()
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

    # The source path is stored in the top-level attachments dict. Check that
    # it matches the value stored on the testcase entry.
    assert attachments[dst_path] == attachment_entry["source_path"]


def test_multi_attach(multi_attachment_plan):
    """
    Test running a Testplan that stores the same attachment multiple times.
    The file only needs to be stored once under the attachments but
    can be referenced from multiple parts of the report.
    """
    plan_result = multi_attachment_plan.run()
    assert plan_result  # Plan should pass.

    report = plan_result.report
    attachments = report.attachments
    assert len(attachments) == 1  # Only one unique file is attached.

    testcase_reports = [suite_report.entries[0]
                        for suite_report in report.entries[0].entries]
    assert len(testcase_reports) == 2

    attachment_entries = [testcase_report.entries[0]
                          for testcase_report in testcase_reports]
    assert len(attachment_entries) == 2

    dst_path = list(attachments.keys())[0]

    # Expect the attachment to be stored as "attachment-[HASH]-[FILESIZE].txt"
    assert re.match(r"attachment-[0-9a-f]+-[0-9]+.txt", dst_path)

    for attachment_entry in attachment_entries:
        assert attachments[dst_path] == attachment_entry["source_path"]

