import os
import datetime
import socket

import six
from schema import Or
from lxml import etree, objectify
from lxml.builder import E  # pylint: disable=no-name-in-module

from testplan.common.config import ConfigOption

from testplan.report import (
    TestGroupReport,
    TestCaseReport,
    ReportCategories,
    RuntimeStatus,
)
from testplan.testing.multitest.entries.assertions import RawAssertion
from testplan.testing.multitest.entries.schemas.base import registry

from ..base import ProcessRunnerTest, ProcessRunnerTestConfig

CPPUNIT_TO_JUNIT_XSL = b"""<?xml version="1.0" encoding="UTF-8"?>
<xsl:stylesheet version="1.0" xmlns:xsl="http://www.w3.org/1999/XSL/Transform">
    <xsl:output method="xml" indent="yes"/>
    <xsl:template match="/">
        <testsuites>
            <xsl:attribute name="name">All Tests</xsl:attribute>
            <testsuite>
                <xsl:attribute name="errors">
                    <xsl:value-of select="TestRun/Statistics/Errors"/>
                </xsl:attribute>
                <xsl:attribute name="failures">
                    <xsl:value-of select="TestRun/Statistics/Failures"/>
                </xsl:attribute>
                <xsl:attribute name="tests">
                    <xsl:value-of select="TestRun/Statistics/Tests"/>
                </xsl:attribute>
                <xsl:attribute name="name"></xsl:attribute>
                <xsl:apply-templates/>
            </testsuite>
        </testsuites>
    </xsl:template>
    <xsl:template match="/TestRun/SuccessfulTests/Test">
        <testcase>
            <xsl:attribute name="classname" ><xsl:value-of select="substring-before(Name, '::')"/></xsl:attribute>
            <xsl:attribute name="name"><xsl:value-of select="substring-after(Name, '::')"/></xsl:attribute>
        </testcase>
    </xsl:template>
    <xsl:template match="/TestRun/FailedTests/FailedTest">
        <testcase>
            <xsl:attribute name="classname" ><xsl:value-of select="substring-before(Name, '::')"/></xsl:attribute>
            <xsl:attribute name="name"><xsl:value-of select="substring-after(Name, '::')"/></xsl:attribute>
            <error>
                <xsl:attribute name="message">
                    <xsl:value-of select=" normalize-space(Message)"/>
                </xsl:attribute>
                <xsl:attribute name="type">
                    <xsl:value-of select="FailureType"/>
                </xsl:attribute>
                <xsl:value-of select="Message"/>
File: <xsl:value-of select="Location/File"/>
Line: <xsl:value-of select="Location/Line"/>
            </error>
        </testcase>
    </xsl:template>
    <xsl:template match="text()|@*"/>
</xsl:stylesheet>
"""


def _set_node_classname(name, element):
    """
    Set classname attribute of tstsuite/testcase if missing or incomplete.

    :param name: Name of Cppunit which will be used as package name.
    :type name: ``str``
    :param element: Xml element on which to set classname (recursively).
    :type element: ``lxml.etree._Element``
    """
    if element.tag == "testcase":
        for key, value in element.items():
            if key == "classname":
                if "." not in value:
                    element.set(key, "{}.{}".format(name, value))
                break
        else:
            element.set("classname", "{0}.{0}".format(name))
    else:
        if element.tag == "testsuite":
            element.set("name", name)
        for child in element.getchildren():
            _set_node_classname(name, child)


class CppunitConfig(ProcessRunnerTestConfig):
    """
    Configuration object for :py:class:`~testplan.testing.cpp.cppunit.Cppunit`.
    """

    @classmethod
    def get_options(cls):
        return {
            ConfigOption("file_output_flag", default="-y"): Or(
                None, lambda x: x.startswith("-")
            ),
            ConfigOption("output_path", default=""): str,
            ConfigOption("filtering_flag", default=None): Or(
                None, lambda x: x.startswith("-")
            ),
            ConfigOption("cppunit_filter", default=""): str,
            ConfigOption("listing_flag", default=None): Or(
                None, lambda x: x.startswith("-")
            ),
            ConfigOption("parse_test_context", default=None): Or(
                None, lambda x: callable(x)
            ),
        }


class Cppunit(ProcessRunnerTest):
    """
    Subprocess test runner for Cppunit: https://sourceforge.net/projects/cppunit

    For original docs please see:

    http://cppunit.sourceforge.net/doc/1.8.0/
    http://cppunit.sourceforge.net/doc/cvs/cppunit_cookbook.html

    Please note that the binary (either native binary or script) should output
    in XML format so that Testplan is able to parse the result. By default
    Testplan reads from stdout, but if `file_output_flag` is set (e.g. "-y"),
    the binary should accept a file path and write the result to that file,
    which will be loaded and parsed by Testplan. For example:

    .. code-block:: bash

        ./cppunit_bin -y /path/to/test/result

    :param name: Test instance name, often used as uid of test entity.
    :type name: ``str``
    :param binary: Path to the application binary or script.
    :type binary: ``str``
    :param description: Description of test instance.
    :type description: ``str``
    :param file_output_flag: Customized command line flag for specifying path
        of output file, default to -y
    :type file_output_flag: ``NoneType`` or ``str``
    :param output_path: Where to save the test report, should work with
        `file_output_flag`, if not provided a default path can be generated.
    :type output_path: ``str``
    :param filtering_flag: Customized command line flag for filtering testcases,
        "-t" is suggested, for example: ./cppunit_bin -t *.some_text.*
    :type filtering_flag: ``NoneType`` or ``str``
    :param cppunit_filter: Native test filter pattern that will be used by
        Cppunit internally.
    :type cppunit_filter: ``str``
    :param listing_flag: Customized command line flag for listing all testcases,
        "-l" is suggested, for example: ./cppunit_bin -l
    :type listing_flag: ``NoneType`` or ``str``
    :param parse_test_context: Function to parse the output which contains
        listed test suites and testcases. refer to the default implementation
        :py:meth:`~testplan.testing.cpp.cppunit.Cppunit.parse_test_context`.
    :type parse_test_context: ``NoneType`` or ``callable``

    Also inherits all
    :py:class:`~testplan.testing.base.ProcessRunnerTest` options.
    """

    CONFIG = CppunitConfig

    def __init__(
        self,
        name,
        binary,
        description=None,
        file_output_flag="-y",
        output_path="",
        filtering_flag=None,
        cppunit_filter="",
        listing_flag=None,
        parse_test_context=None,
        **options
    ):
        options.update(self.filter_locals(locals()))
        super(Cppunit, self).__init__(**options)

    @property
    def report_path(self):
        if self.cfg.file_output_flag and self.cfg.output_path:
            return self.cfg.output_path
        else:
            return os.path.join(self._runpath, "report.xml")

    def test_command(self):
        cmd = [self.cfg.binary]
        if self.cfg.filtering_flag and self.cfg.cppunit_filter:
            cmd.extend([self.cfg.filtering_flag, self.cfg.cppunit_filter])
        if self.cfg.file_output_flag:
            cmd.extend([self.cfg.file_output_flag, self.report_path])
        return cmd

    def list_command(self):
        if self.cfg.listing_flag:
            return [self.cfg.binary, self.cfg.listing_flag]
        else:
            return super(Cppunit, self).list_command()

    def read_test_data(self):
        """
        Parse XML report generated by Cppunit test and return the root node.
        XML report should be compatible with xUnit format.

        :return: Root node of parsed raw test data
        :rtype: ``xml.etree.Element``
        """
        with open(
            self.report_path if self.cfg.file_output_flag else self.stdout
        ) as report_file:
            return objectify.fromstring(
                self.cppunit_to_junit(
                    report_file.read(), self._DEFAULT_SUITE_NAME
                )
            )

    def process_test_data(self, test_data):
        """
        XML output contains entries for skipped testcases
        as well, which are not included in the report.
        """
        result = []

        for suite in test_data.getchildren():
            suite_name = suite.attrib["name"]
            suite_report = TestGroupReport(
                name=suite_name,
                uid=suite_name,
                category=ReportCategories.TESTSUITE,
            )

            for testcase in suite.getchildren():
                if testcase.tag != "testcase":
                    continue

                testcase_classname = testcase.attrib["classname"]
                testcase_name = testcase.attrib["name"]
                testcase_prefix = testcase_classname.split(".")[-1]
                testcase_report = TestCaseReport(
                    name="{}::{}".format(testcase_prefix, testcase_name),
                    uid="{}::{}".format(
                        testcase_classname.replace(".", "::"), testcase_name
                    ),
                )

                if not testcase.getchildren():
                    assertion_obj = RawAssertion(
                        description="Passed",
                        content="Testcase {} passed".format(testcase_name),
                        passed=True,
                    )
                    testcase_report.append(registry.serialize(assertion_obj))
                else:
                    for entry in testcase.getchildren():
                        assertion_obj = RawAssertion(
                            description=entry.tag,
                            content=entry.text,
                            passed=entry.tag not in ("failure", "error"),
                        )
                        testcase_report.append(
                            registry.serialize(assertion_obj)
                        )

                testcase_report.runtime_status = RuntimeStatus.FINISHED
                suite_report.append(testcase_report)

            if len(suite_report) > 0:
                result.append(suite_report)

        return result

    def parse_test_context(self, test_list_output):
        """
        Default implementation of parsing Cppunit test listing from stdout.
        Assume the format of output is like that of GTest listing. If the
        Cppunit test lists the test suites and testcases in other format,
        then this function needs to be re-implemented.
        """
        # Sample command line output:
        #
        # Comparison.
        #   testNotEqual
        #   testGreater
        #   testLess
        #   testMisc
        # LogicalOp.
        #   testOr
        #   testAnd
        #   testNot
        #   testXor
        #
        #
        # Sample Result:
        #
        # [
        #     ['Comparison',
        #        ['testNotEqual', 'testGreater', 'testLess', 'testMisc']],
        #     ['LogicalOp', ['testOr', 'testAnd', 'testNot', 'testXor']],
        # ]
        if self.cfg.parse_test_context:
            return self.cfg.parse_test_context(test_list_output)

        # Default implementation: suppose that the output of
        # listing testcases is the same like that of GTest.
        result = []
        for line in test_list_output.splitlines():
            line = line.rstrip()
            if line.endswith(".") and len(line.lstrip()) > 1:
                result.append([line.lstrip()[:-1], []])
            elif result and (line.startswith(" ") or line.startswith("\t")):
                result[-1][1].append(line.lstrip())
        return result

    def update_test_report(self):
        """
        Attach XML report contents to the report, which can be
        used by XML exporters, but will be discarded by serializers.
        """
        super(Cppunit, self).update_test_report()

        try:
            with open(
                self.report_path if self.cfg.file_output_flag else self.stdout
            ) as report_xml:
                self.result.report.xml_string = report_xml.read()
        except Exception:
            self.result.report.xml_string = ""

    def test_command_filter(self, testsuite_pattern, testcase_pattern):
        """
        Return the base test command with additional filtering to run a
        specific set of testcases.
        """
        if testsuite_pattern not in (
            "*",
            self._DEFAULT_SUITE_NAME,
            self._VERIFICATION_SUITE_NAME,
        ):
            raise RuntimeError("Cannot run individual test suite")
        if testcase_pattern not in ("*", self._VERIFICATION_TESTCASE_NAME):
            self.logger.debug(
                'Should run testcases in pattern "%s", but cannot run'
                " individual testcase thus will run the whole test suite",
                testcase_pattern,
            )
        return self.test_command()

    @staticmethod
    def cppunit_to_junit(report, name):
        """
        Transform cppunit xml into junit compatible xml.
        TODO: can be moved to `testplan.common.util.xml module` if add more
        similar functions that are needed by unit test binaries.

        :param report: Cppunit test report in XML format.
        :type report: ``str``
        :param name: Name of Cppunit which is used to set classname on XML
            element recursively.
        :type name: ``str``
        """
        transform = etree.XSLT(etree.XML(CPPUNIT_TO_JUNIT_XSL))
        cppunit_report = etree.XML(six.ensure_binary(report))
        junit_report = transform(cppunit_report)
        _set_node_classname(name, junit_report.getroot().getchildren()[0])

        for testsuite in junit_report.xpath("//testsuite"):
            if not testsuite.xpath("/properties"):
                testsuite.insert(0, E.properties())
            if not testsuite.xpath("/system-out"):
                testsuite.append(etree.Element("system-out"))
            if not testsuite.xpath("/system-err"):
                testsuite.append(etree.Element("system-err"))
            if testsuite.get("timestamp") is None:
                testsuite.set(
                    "timestamp",
                    datetime.datetime.utcnow().isoformat().split(".")[0],
                )
            if testsuite.get("hostname") is None:
                testsuite.set("hostname", socket.gethostname())
            if testsuite.get("time") is None:
                testsuite.set("time", "0")

        for testcase in junit_report.xpath("//testsuite/testcase"):
            if testcase.get("time") is None:
                testcase.set("time", "0")

        return etree.tostring(junit_report)
