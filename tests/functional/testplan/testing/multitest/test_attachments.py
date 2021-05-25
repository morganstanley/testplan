"""Test storing of attachments in a report."""
import re
import os

import pytest

import testplan
from testplan.testing import multitest


@multitest.testsuite
class Suite1(object):
    def __init__(self, attachments):
        self._attachments = attachments

    @multitest.testcase
    def attach(self, env, result):
        for attachment in self._attachments:
            result.attach(attachment, description="attaching a file")


@pytest.fixture(scope="function")
def attachment_plan(tmpdir):
    attachment_path = str(tmpdir.join("attachment.txt"))
    with open(attachment_path, "w") as f:
        f.write("testplan\n")

    plan = testplan.TestplanMock(name="AttachmentPlan")
    plan.add(
        multitest.MultiTest(
            name="AttachmentTest", suites=[Suite1([attachment_path])]
        )
    )
    return plan


@pytest.fixture(scope="function")
def multi_attachments_plan(tmpdir):

    attachment_paths = [
        str(tmpdir.mkdir(f"{i}").join("attachment.txt")) for i in range(2)
    ]

    # Write different content to each file to ensure they get a unique hash.
    for i, attachment_path in enumerate(attachment_paths):
        with open(attachment_path, "w") as f:
            f.write(f"testplan{i}\n")

    plan = testplan.TestplanMock(name="AttachmentPlan")
    plan.add(
        multitest.MultiTest(
            name="AttachmentTest",
            suites=[Suite1(attachment_paths)],
        )
    )
    return plan


@pytest.fixture(scope="function")
def same_attachments_plan(tmpdir):
    attachment_path = str(tmpdir.join("attachment.txt"))
    with open(attachment_path, "w") as f:
        f.write("testplan\n")

    plan = testplan.TestplanMock(name="AttachmentPlan")
    plan.add(
        multitest.MultiTest(
            name="AttachmentTest",
            suites=[Suite1([attachment_path] * 2)],
        )
    )
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


def test_multi_attachments(multi_attachments_plan):
    """
    Test running a Testplan that stores unique attachments multiple times.
    """
    plan_result = multi_attachments_plan.run()
    assert plan_result  # Plan should pass.

    report = plan_result.report
    attachments = report.attachments
    assert len(attachments) == 2  # Two unique file attachments

    testcase_report = report.entries[0].entries[0].entries[0]

    assert len(testcase_report.entries) == 2

    for i in range(2):
        entry = testcase_report.entries[i]
        dst_path = entry["dst_path"]
        with open(entry["source_path"], "r") as fd:
            content = fd.read()
            assert content == f"testplan{i}\n"

        # Expect the attachment to be stored as
        # "attachment-[HASH]-[FILESIZE].txt"
        assert re.match(r"attachment-[0-9a-f]+-[0-9]+.txt", dst_path)

        # Check that the source and dst paths match.
        assert attachments[dst_path] == entry["source_path"]


def test_same_attachments(same_attachments_plan):
    """
    Test running a Testplan that stores the same attachment multiple times.
    The file only needs to be stored once under the attachments but
    can be referenced from multiple parts of the report.
    """
    plan_result = same_attachments_plan.run()
    assert plan_result  # Plan should pass.

    report = plan_result.report
    attachments = report.attachments
    assert len(attachments) == 1  # Only one unique file is attached.

    attachment_entries = report.entries[0].entries[0].entries[0].entries
    assert len(attachment_entries) == 2

    dst_path = list(attachments.keys())[0]

    # Expect the attachment to be stored as "attachment-[HASH]-[FILESIZE].txt"
    assert re.match(r"attachment-[0-9a-f]+-[0-9]+.txt", dst_path)

    for attachment_entry in attachment_entries:
        assert attachments[dst_path] == attachment_entry["source_path"]
