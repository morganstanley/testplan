"""Test storing of attachments in a report."""
import tempfile
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


@pytest.fixture(scope="module")
def attachment_plan():
    with tempfile.NamedTemporaryFile(
            mode="w", suffix=".txt", delete=False) as tmpfile:
        tmpfile.write("testplan\n" * 100)

    try:
        plan = testplan.Testplan(name="AttachmentPlan", parse_cmdline=False)
        plan.add(multitest.MultiTest(
                name="AttachmentTest",
                suites=[Suite(tmpfile.name)]))
        yield plan, tmpfile.name
    finally:
        os.remove(tmpfile.name)


def test_attach(attachment_plan):
    """Test running a Testplan that stores a single attachment."""
    plan, tmpfile_path = attachment_plan
    plan_result = plan.run()
    assert plan_result  # Plan should pass.

    report = plan_result.report
    attachments = report.attachments
    testcase_report = report.entries[0].entries[0].entries[0]
    assert testcase_report.name == "attach"
    assert len(testcase_report.entries) == 1

    attachment_entry = testcase_report.entries[0]

    filename = attachment_entry["filename"]
    uuid = attachment_entry["uuid"]
    dst_path = attachment_entry["dst_path"]

    assert dst_path == os.path.join(uuid, filename)
    assert attachments[dst_path] == attachment_entry["source_path"]
