"""Test the JSON exporter."""
import json
import os
import hashlib
import tempfile

from testplan.testing import multitest

from testplan import TestplanMock
from testplan.common.utils.testing import argv_overridden
from testplan.exporters.testing import JSONExporter


@multitest.testsuite
class Alpha(object):
    @multitest.testcase
    def test_comparison(self, env, result):
        result.equal(1, 1, "equality description")

    @multitest.testcase
    def test_membership(self, env, result):
        result.contain(1, [1, 2, 3])

    @multitest.testcase
    def test_attach(self, env, result):
        """Test attaching a file to the report."""
        with tempfile.NamedTemporaryFile(mode="w", delete=False) as tmpfile:
            tmpfile.write("testplan\n" * 100)

        result.attach(tmpfile.name)


@multitest.testsuite
class Beta(object):
    @multitest.testcase
    def test_failure(self, env, result):
        result.equal(1, 2, "failing assertion")
        result.not_equal(5, 5)

    @multitest.testcase
    def test_error(self, env, result):
        raise Exception("foo")


def test_json_exporter(runpath):
    """
    JSON Exporter should generate a json report at the given `json_path`.
    """
    json_path = os.path.join(runpath, "report.json")

    plan = TestplanMock(
        "plan", exporters=JSONExporter(json_path=json_path), runpath=runpath
    )
    multitest_1 = multitest.MultiTest(name="Primary", suites=[Alpha()])
    multitest_2 = multitest.MultiTest(name="Secondary", suites=[Beta()])
    plan.add(multitest_1)
    plan.add(multitest_2)
    plan.run()

    assert os.path.exists(json_path)
    assert os.stat(json_path).st_size > 0

    # Load the JSON file to validate it contains valid JSON.
    with open(json_path) as json_file:
        report = json.load(json_file)

    # Check that the expected text file is attached correctly.
    attachments_dir = os.path.join(os.path.dirname(json_path), "_attachments")
    assert os.path.isdir(attachments_dir)
    assert len(report["attachments"]) == 1

    dst_path = list(report["attachments"].keys())[0]
    attachment_filepath = os.path.join(attachments_dir, dst_path)
    assert os.path.isfile(attachment_filepath)

    with open(attachment_filepath) as f:
        attachment_file_contents = f.read()
    assert attachment_file_contents == "testplan\n" * 100


def test_json_exporter_split_report(runpath):
    """
    JSON Exporter should generate a json report at the given `json_path`.
    """
    json_path = os.path.join(runpath, "report.json")

    plan = TestplanMock(
        "plan",
        exporters=[JSONExporter(json_path=json_path, split_json_report=True)],
        runpath=runpath,
    )

    multitest_1 = multitest.MultiTest(name="Primary", suites=[Alpha()])
    multitest_2 = multitest.MultiTest(name="Secondary", suites=[Beta()])
    plan.add(multitest_1)
    plan.add(multitest_2)
    plan.run()

    assert os.path.exists(json_path)
    assert os.stat(json_path).st_size > 0

    # Load the JSON file to validate it contains valid JSON.
    with open(json_path) as json_file:
        report = json.load(json_file)
    assert report["split"] == True

    # Check that the expected text file is attached correctly.
    attachments_dir = os.path.join(os.path.dirname(json_path), "_attachments")
    assert os.path.isdir(attachments_dir)
    assert len(report["entries"]) == 0
    assert len(report["attachments"]) == 3

    digest = hashlib.md5(json_path.encode("utf-8")).hexdigest()
    attachment_1 = "report-structure-{}.json".format(digest)
    attachment_2 = "report-assertions-{}.json".format(digest)
    assert attachment_1 in report["attachments"]
    assert attachment_2 in report["attachments"]

    attachment_filepath_1 = os.path.join(attachments_dir, attachment_1)
    attachment_filepath_2 = os.path.join(attachments_dir, attachment_2)
    assert os.path.isfile(attachment_filepath_1)
    assert os.path.isfile(attachment_filepath_2)

    with open(attachment_filepath_1) as f1, open(attachment_filepath_2) as f2:
        structure = json.loads(f1.read())
        assertions = json.loads(f2.read())

    assert len(structure) == 2  # 2 multitests
    assert structure[0]["name"] == "Primary"  # 1st multitest name
    assert len(structure[0]["entries"]) == 1  # one suite in 1st multitest
    assert structure[0]["entries"][0]["name"] == "Alpha"  # 1st suite name
    assert len(structure[0]["entries"][0]["entries"]) == 3  # 3 testcases
    assert structure[1]["name"] == "Secondary"  # 2nd multitest name
    assert len(structure[1]["entries"]) == 1  # one suite in 2nd multitest
    assert structure[1]["entries"][0]["name"] == "Beta"  # 1st suite name
    assert len(structure[1]["entries"][0]["entries"]) == 2  # 2 testcases

    assert len(assertions["plan"]) == 2
    assert len(assertions["plan"]["Primary"]) == 1
    assert len(assertions["plan"]["Primary"]["Alpha"]) == 3
    assert len(assertions["plan"]["Secondary"]) == 1
    assert len(assertions["plan"]["Secondary"]["Beta"]) == 2

    # only one assertion in each testcase in suite `Alpha`
    assert (
        assertions["plan"]["Primary"]["Alpha"]["test_comparison"][0]["type"]
        == "Equal"
    )
    assert (
        assertions["plan"]["Primary"]["Alpha"]["test_membership"][0]["type"]
        == "Contain"
    )
    assert (
        assertions["plan"]["Primary"]["Alpha"]["test_attach"][0]["type"]
        == "Attachment"
    )
    # 2 assertions in testcase `test_failure`
    assert (
        assertions["plan"]["Secondary"]["Beta"]["test_failure"][0]["type"]
        == "Equal"
    )
    assert (
        assertions["plan"]["Secondary"]["Beta"]["test_failure"][1]["type"]
        == "NotEqual"
    )
    # no assertion in testcase `test_error`
    assert len(assertions["plan"]["Secondary"]["Beta"]["test_error"]) == 0


def test_implicit_exporter_initialization(runpath):
    """
    An implicit JSON should be generated if `json_path` is available
    via cmdline args but no exporters were declared programmatically.
    """
    json_path = os.path.join(runpath, "report.json")

    with argv_overridden("--json", json_path):
        plan = TestplanMock(name="plan", parse_cmdline=True)
        multitest_1 = multitest.MultiTest(name="Primary", suites=[Alpha()])
        plan.add(multitest_1)
        plan.run()

    assert os.path.exists(json_path)
    assert os.stat(json_path).st_size > 0

    # Load the JSON file to validate it contains valid JSON.
    with open(json_path) as json_file:
        json.load(json_file)
