"""Test the JSON exporter."""
import os
import json
import copy
import tempfile
import pathlib

from testplan import TestplanMock
from testplan.testing import multitest
from testplan.common.utils.testing import argv_overridden
from testplan.exporters.testing import JSONExporter
from testplan.exporters.testing.json import gen_attached_report_names


full_report = {
    "python_version": "3.7.5",
    "category": "testplan",
    "runtime_status": "finished",
    "status": "failed",
    "entries": [
        {
            "category": "multitest",
            "parent_uids": ["Multiply"],
            "name": "MultiplyTest",
            "uid": "MultiplyTest",
            "entries": [
                {
                    "category": "testsuite",
                    "parent_uids": ["Multiply", "MultiplyTest"],
                    "name": "BasicSuite",
                    "uid": "BasicSuite",
                    "entries": [
                        {
                            "category": "parametrization",
                            "parent_uids": [
                                "Multiply",
                                "MultiplyTest",
                                "BasicSuite",
                            ],
                            "name": "Basic Multiply",
                            "uid": "basic_multiply",
                            "entries": [
                                {
                                    "entries": [
                                        {
                                            "name": "test assertion1",
                                            "uid": "test_assertion1",
                                        },
                                    ],
                                    "type": "TestCaseReport",
                                    "category": "testcase",
                                    "parent_uids": [
                                        "Multiply",
                                        "MultiplyTest",
                                        "BasicSuite",
                                        "basic_multiply",
                                    ],
                                    "name": "basic multiply <p1='aaa', p2=111>",
                                    "uid": "basic_multiply__p1_aaa__p2_111",
                                },
                                {
                                    "entries": [
                                        {
                                            "name": "test assertion2",
                                            "uid": "test_assertion2",
                                        }
                                    ],
                                    "type": "TestCaseReport",
                                    "category": "testcase",
                                    "parent_uids": [
                                        "Multiply",
                                        "MultiplyTest",
                                        "BasicSuite",
                                        "basic_multiply",
                                    ],
                                    "name": "basic multiply <p1='bbb', p2=222>",
                                    "uid": "basic_multiply__p1_bbb__p2_222",
                                },
                            ],
                            "type": "TestGroupReport",
                        }
                    ],
                    "type": "TestGroupReport",
                }
            ],
            "type": "TestGroupReport",
        }
    ],
    "name": "Multiply",
    "uid": "Multiply",
    "project": "testplan",
    "timeout": 14400,
}


meta_part = {
    "python_version": "3.7.5",
    "category": "testplan",
    "runtime_status": "finished",
    "status": "failed",
    "entries": [],
    "name": "Multiply",
    "uid": "Multiply",
    "project": "testplan",
    "timeout": 14400,
}


structure_part = [
    {
        "category": "multitest",
        "parent_uids": ["Multiply"],
        "name": "MultiplyTest",
        "uid": "MultiplyTest",
        "entries": [
            {
                "category": "testsuite",
                "parent_uids": ["Multiply", "MultiplyTest"],
                "name": "BasicSuite",
                "uid": "BasicSuite",
                "entries": [
                    {
                        "category": "parametrization",
                        "parent_uids": [
                            "Multiply",
                            "MultiplyTest",
                            "BasicSuite",
                        ],
                        "name": "Basic Multiply",
                        "uid": "basic_multiply",
                        "entries": [
                            {
                                "entries": [],
                                "type": "TestCaseReport",
                                "category": "testcase",
                                "parent_uids": [
                                    "Multiply",
                                    "MultiplyTest",
                                    "BasicSuite",
                                    "basic_multiply",
                                ],
                                "name": "basic multiply <p1='aaa', p2=111>",
                                "uid": "basic_multiply__p1_aaa__p2_111",
                            },
                            {
                                "entries": [],
                                "type": "TestCaseReport",
                                "category": "testcase",
                                "parent_uids": [
                                    "Multiply",
                                    "MultiplyTest",
                                    "BasicSuite",
                                    "basic_multiply",
                                ],
                                "name": "basic multiply <p1='bbb', p2=222>",
                                "uid": "basic_multiply__p1_bbb__p2_222",
                            },
                        ],
                        "type": "TestGroupReport",
                    }
                ],
                "type": "TestGroupReport",
            }
        ],
        "type": "TestGroupReport",
    }
]


assertions_part = {
    "basic_multiply__p1_aaa__p2_111": [
        {"name": "test assertion1", "uid": "test_assertion1"},
    ],
    "basic_multiply__p1_bbb__p2_222": [
        {"name": "test assertion2", "uid": "test_assertion2"},
    ],
}


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


def test_split_and_merge():
    """
    Test static methods used for splitting and merging JSON report.
    """
    meta, structure, assertions = JSONExporter.split_json_report(
        copy.deepcopy(full_report)
    )
    assert meta == meta_part
    assert structure == structure_part
    assert assertions == assertions_part
    assert (
        JSONExporter.merge_json_report(meta, structure, assertions)
        == full_report
    )


def test_json_exporter(runpath):
    """
    JSON Exporter should generate a full json report at the given `json_path`.
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
    # attachments_dir = os.path.join(os.path.dirname(json_path), "_attachments")
    attachments_dir = os.path.join(os.path.dirname(json_path), "plan")
    assert os.path.isdir(attachments_dir)
    assert len(report["attachments"]) == 1

    dst_path = list(report["attachments"].keys())[0]
    attachment_filepath = os.path.join(attachments_dir, dst_path)
    assert os.path.isfile(attachment_filepath)

    with open(attachment_filepath) as f:
        attachment_file_contents = f.read()
    assert attachment_file_contents == "testplan\n" * 100


def test_json_exporter_generating_split_report(runpath):
    """
    JSON Exporter should generate a main json report at the given `json_path`.
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

    assert report["version"] == 2

    # Check that the expected text file is attached correctly.
    attachments_dir = os.path.join(os.path.dirname(json_path), "plan")
    assert os.path.isdir(attachments_dir)
    assert len(report["entries"]) == 0
    assert len(report["attachments"]) == 3

    structure_filename, assertions_filename = gen_attached_report_names(
        json_path
    )
    assert structure_filename in report["attachments"]
    assert assertions_filename in report["attachments"]
    assert report["structure_file"] == structure_filename
    assert report["assertions_file"] == assertions_filename

    structure_filepath = os.path.join(attachments_dir, structure_filename)
    assertions_filepath = os.path.join(attachments_dir, assertions_filename)
    assert os.path.isfile(structure_filepath)
    assert os.path.isfile(assertions_filepath)

    with open(structure_filepath) as f1, open(assertions_filepath) as f2:
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

    assert len(assertions) == 5  # 5 assertions in total
    # only one assertion in each testcase in suite `Alpha`
    assert assertions["test_comparison"][0]["type"] == "Equal"
    assert assertions["test_membership"][0]["type"] == "Contain"
    assert assertions["test_attach"][0]["type"] == "Attachment"
    # 2 assertions in testcase `test_failure`
    assert assertions["test_failure"][0]["type"] == "Equal"
    assert assertions["test_failure"][1]["type"] == "NotEqual"
    # no assertion in testcase `test_error`
    assert len(assertions["test_error"]) == 0


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
