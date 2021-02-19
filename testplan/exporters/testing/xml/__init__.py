"""
    XML Export logic for test reports.
"""
import os
import socket
import shutil
from collections import Counter

from lxml import etree
from lxml.builder import E  # pylint: disable=no-name-in-module

from testplan.common.utils.path import unique_name
from testplan.common.utils.strings import slugify

from testplan.common.config import ConfigOption
from testplan.common.exporters import ExporterConfig

from testplan.report import (
    TestCaseReport,
    TestGroupReport,
    ReportCategories,
    Status,
)

from ..base import Exporter


class BaseRenderer(object):
    """
    Basic renderer, will render a test group report with the following
    structure:

    .. code-block:: python

      TestGroupReport(name=..., category='<test-category>')
          TestGroupReport(name=..., category='testsuite')
              TestCaseReport(name=...)  (failing)
                  RawAssertion (dict form)
              TestCaseReport(name=...) (passing)
              TestCaseReport(name=...) (passing)
    """

    def render(self, source):
        """
        Top level rendering logic, renders each suite
        separately & groups them within `testsuites` tag.
        """
        testsuites = []
        counter = Counter({})

        for index, suite_report in enumerate(source):
            counter += suite_report.counter
            suite_elem = self.render_testsuite(index, source, suite_report)
            testsuites.append(suite_elem)

        return E.testsuites(
            *testsuites,
            tests=str(counter["total"]),
            errors=str(counter["error"]),
            failures=str(counter["failed"])
        )

    def get_testcase_reports(self, testsuite_report):
        """
        Get testcases from a suite report, normally this is more or less
        equal to all children of the suite report, however certain test
        runners (e.g. MultiTest) may have nested data that needs to be
        flattened.
        """
        for child in testsuite_report:
            if isinstance(child, TestCaseReport):
                yield child
            elif isinstance(child, TestGroupReport):
                # Recurse - yield each of the testcases in this group.
                for testcase in self.get_testcase_reports(child):
                    yield testcase
            else:
                raise TypeError("Unsupported report type: {}".format(child))

    def render_testsuite(self, index, test_report, testsuite_report):
        """
        Render a single testsuite with its testcases within a `testsuite`
        tag.
        """
        cases = [
            self.render_testcase(
                test_report, testsuite_report, testcase_report
            )
            for testcase_report in self.get_testcase_reports(testsuite_report)
        ]

        return E.testsuite(
            *cases,
            hostname=socket.gethostname(),
            id=str(index),
            package="{}:{}".format(test_report.name, testsuite_report.name),
            name=testsuite_report.name,
            errors=str(testsuite_report.counter["error"]),
            failures=str(testsuite_report.counter["failed"]),
            tests=str(testsuite_report.counter["total"])
        )

    def render_testcase(self, test_report, testsuite_report, testcase_report):
        """
        Render a testcase with errors & failures within a `testcase`
        tag.
        """
        # the xsd for junit only allows errors OR failures not both
        if testcase_report.status == Status.ERROR:
            details = self.render_testcase_errors(testcase_report)
        elif testcase_report.status == Status.FAILED:
            details = self.render_testcase_failures(testcase_report)
        else:
            details = []

        return E.testcase(
            *details,
            name=testcase_report.name,
            classname="{}:{}:{}".format(
                test_report.name, testsuite_report.name, testcase_report.name
            ),
            time=str(testcase_report.timer["run"].elapsed)
            if "run" in testcase_report.timer
            else "0"
        )

    def render_testcase_errors(self, testcase_report):
        """
        Create an `error` tag that holds error information via testcase
        report's logs.
        """
        return [
            E.error(message=log["message"])
            for log in testcase_report.logs
            if log["levelname"] == "ERROR"
        ]

    def render_testcase_failures(self, testcase_report):
        """
        Entries of a testcase report are in dict form, which may
        also be nested in case there are groups/summaries.

        This method flattens the enty data and iterates over failing
        assertions to create `failure` tags with element tree.
        """
        # Depth does not matter, we just need entries in flat form
        flat_dicts = list(zip(*testcase_report.flattened_entries(depth=0)))[1]

        failed_assertions = [
            entry
            for entry in flat_dicts
            # Only get failing assertions
            if entry["meta_type"] == "assertion" and not entry["passed"] and
            # Groups have no use in XML output
            not entry["type"] in ("Group", "Summary")
        ]

        failures = []
        for entry in failed_assertions:
            failure = E.failure(
                message=entry["description"] or entry["type"], type="assertion"
            )
            if entry["type"] == "RawAssertion":
                failure.text = etree.CDATA(entry["content"])
            failures.append(failure)

        return failures


class MultiTestRenderer(BaseRenderer):
    """
    Source report represents a MultiTest with the following structure:

    .. code-block:: python

      TestGroupReport(name=..., category='multitest')
          TestGroupReport(name=..., category='testsuite')
              TestCaseReport(name=...)
                  Assertion entry (dict)
                  Assertion entry (dict)
              TestGroupReport(name='...', category='parametrization')
                  TestCaseReport(name=...)
                      Assertion entry (dict)
                      Assertion entry (dict)
                  TestCaseReport(name=...)
                      Assertion entry (dict)
                      Assertion entry (dict)

    Final XML will have flattened testcase data from parametrization groups.
    """

    def get_testcase_reports(self, testsuite_report):
        """
        Multitest suites may have additional nested in case of
        parametrization.
        """
        testcase_reports = []
        for child in testsuite_report:
            if isinstance(child, TestCaseReport):
                testcase_reports.append(child)
            elif (
                isinstance(child, TestGroupReport)
                and child.category == ReportCategories.PARAMETRIZATION
            ):
                testcase_reports.extend(child.entries)
            else:
                raise TypeError("Unsupported report type: {}".format(child))
        return testcase_reports


class XMLExporterConfig(ExporterConfig):
    """
    Configuration object for
    :py:class:`XMLExporter <testplan.exporters.testing.xml.XMLExporter>`
    object.
    """

    @classmethod
    def get_options(cls):
        return {ConfigOption("xml_dir"): str}


class XMLExporter(Exporter):
    """
    XML Exporter. Produces one XML file per each child of
    TestPlanReport (e.g. Multitest reports)

    :param xml_dir: Directory for saving xml reports.
    :type xml_dir: ``str``

    Also inherits all
    :py:class:`~testplan.exporters.testing.base.Exporter` options.
    """

    CONFIG = XMLExporterConfig

    renderer_map = {ReportCategories.MULTITEST: MultiTestRenderer}

    def __init__(self, name="XML exporter", **options):
        super(XMLExporter, self).__init__(name=name, **options)

    def export(self, source):
        """
        Create multiple XML files in the given directory for each top
        level test group report.
        """
        xml_dir = self.cfg.xml_dir

        if os.path.exists(xml_dir):
            shutil.rmtree(xml_dir)

        os.makedirs(xml_dir)

        files = set(os.listdir(xml_dir))

        for child_report in source:
            filename = "{}.xml".format(slugify(child_report.name))
            filename = unique_name(filename, files)
            files.add(filename)
            file_path = os.path.join(xml_dir, filename)

            # If a report has XML string attribute it was mostly
            # generated via parsing a JUnit compatible XML file
            # already, meaning we don't need to re-generate the XML
            # contents, but can directly write the contents to a file
            # instead.
            if hasattr(child_report, "xml_string"):
                with open(file_path, "w") as xml_target:
                    xml_target.write(child_report.xml_string)
            else:
                renderer = self.renderer_map.get(
                    child_report.category, BaseRenderer
                )()
                element = etree.ElementTree(renderer.render(child_report))
                element.write(
                    file_path,
                    pretty_print=True,
                    xml_declaration=True,
                    encoding="UTF-8",
                )

        xml_dir = os.path.abspath(xml_dir)
        self.logger.exporter_info(
            "%s XML files created at %s", len(source), xml_dir
        )
        return xml_dir
