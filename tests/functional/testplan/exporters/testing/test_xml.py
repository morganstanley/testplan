import os
import re

from testplan.testing import multitest

from testplan import TestplanMock
from testplan.common.exporters import ExportContext
from testplan.common.utils.testing import argv_overridden, XMLComparison as XC
from testplan.exporters.testing import XMLExporter
from testplan.report import (
    TestReport,
    TestCaseReport,
    TestGroupReport,
    ReportCategories,
)

FLOAT_PATTERN = r"{d}+\.?d{d}+"
export_context = ExportContext()


@multitest.testsuite
class Alpha:
    @multitest.testcase
    def test_comparison(self, env, result):
        result.equal(1, 1, "equality description")

    @multitest.testcase
    def test_membership(self, env, result):
        result.contain(1, [1, 2, 3])


@multitest.testsuite
class Beta:
    @multitest.testcase
    def test_failure(self, env, result):
        result.equal(1, 2, "failing assertion")
        result.equal(5, 10)

    @multitest.testcase
    def test_error(self, env, result):
        raise Exception("foo")


def test_xml_exporter(tmpdir):
    """
    XMLExporter should create a JUnit compatible xml file for each
    multitest in the plan.
    """
    xml_dir = tmpdir.mkdir("xml")

    plan = TestplanMock(
        name="plan", exporters=XMLExporter(xml_dir=xml_dir.strpath)
    )
    multitest_1 = multitest.MultiTest(name="Primary", suites=[Alpha()])
    multitest_2 = multitest.MultiTest(name="Secondary", suites=[Beta()])
    plan.add(multitest_1)
    plan.add(multitest_2)
    plan.run()

    xml_primary = xml_dir.join("primary.xml").strpath
    xml_secondary = xml_dir.join("secondary.xml").strpath

    xml_primary_comparison = XC(
        tag="testsuites",
        children=[
            XC(
                tag="testsuite",
                tests="2",
                errors="0",
                name="Alpha",
                package="Primary:Alpha",
                hostname=re.compile(".+"),
                failures="0",
                id="0",
                children=[
                    XC(
                        tag="testcase",
                        classname="Primary:Alpha:test_comparison",
                        name="test_comparison",
                        time=re.compile(r"\d+\.?\d*"),
                    ),
                    XC(
                        tag="testcase",
                        classname="Primary:Alpha:test_membership",
                        name="test_membership",
                        time=re.compile(r"\d+\.?\d*"),
                    ),
                ],
            )
        ],
    )

    xml_secondary_comparison = XC(
        tag="testsuites",
        children=[
            XC(
                tag="testsuite",
                tests="2",
                errors="1",
                name="Beta",
                package="Secondary:Beta",
                hostname=re.compile(".+"),
                failures="1",
                id="0",
                children=[
                    XC(
                        tag="testcase",
                        classname="Secondary:Beta:test_failure",
                        name="test_failure",
                        time=re.compile(r"\d+\.?\d*"),
                        children=[
                            XC(
                                tag="failure",
                                message="failing assertion",
                                type="assertion",
                            ),
                            XC(
                                tag="failure",
                                message="5 == 10",
                                type="assertion",
                            ),
                        ],
                    ),
                    XC(
                        tag="testcase",
                        classname="Secondary:Beta:test_error",
                        name="test_error",
                        time=re.compile(r"\d+\.?\d*"),
                        children=[
                            XC(
                                tag="error",
                                message=re.compile(
                                    r"Traceback(.|\n)+Exception:(\s)+foo"
                                ),
                            )
                        ],
                    ),
                ],
            )
        ],
    )

    test_ctx = (
        (xml_primary, xml_primary_comparison),
        (xml_secondary, xml_secondary_comparison),
    )

    for file_path, xml_comparison in test_ctx:
        with open(file_path) as xml_file:
            xml_comparison.compare(xml_file.read())


sample_report = TestReport(
    name="my testplan",
    entries=[
        TestGroupReport(
            name="My Multitest",
            category=ReportCategories.MULTITEST,
            entries=[
                TestGroupReport(
                    name="MySuite",
                    category=ReportCategories.TESTSUITE,
                    entries=[TestCaseReport(name="my_test_method")],
                )
            ],
        )
    ],
)


def test_xml_exporter_cleanup(tmpdir):
    """
    XMLExporter should purge & recreate XML dir.
    """

    xml_dir = tmpdir.mkdir("xml")

    assert os.listdir(xml_dir.strpath) == []

    open(xml_dir.join("foo.txt").strpath, "a").close()

    XMLExporter(xml_dir=xml_dir.strpath).export(
        source=sample_report, export_context=export_context
    )

    assert os.listdir(xml_dir.strpath) == ["my-multitest.xml"]


def test_implicit_exporter_initialization(tmpdir):
    """
    An implicit XMLExporter should be generated if `xml_dir` is available
    via cmdline args but no exporters were declared programmatically.
    """
    xml_dir = tmpdir.mkdir("xml")

    with argv_overridden("--xml", xml_dir.strpath):
        plan = TestplanMock(name="plan", parse_cmdline=True)
        multitest_1 = multitest.MultiTest(name="Primary", suites=[Alpha()])
        plan.add(multitest_1)
        plan.run()

    xml_path = xml_dir.join("primary.xml").strpath

    assert os.path.exists(xml_path)
    assert os.stat(xml_path).st_size > 0
