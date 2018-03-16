"""
    XML Export logic for test reports.
"""
import socket
import os
import shutil

from lxml import etree
from lxml.builder import E

from schema import Schema, Or

from testplan import defaults
from testplan.logger import TESTPLAN_LOGGER
from testplan.common.utils.path import unique_name
from testplan.common.utils.strings import slugify

from testplan.common.config import ConfigOption
from testplan.common.exporters import ExporterConfig

from testplan.report.testing import TestCaseReport, TestGroupReport
from testplan.testing.multitest.base import Categories, Status

from ..base import Exporter


class MultiTestRenderer(object):
    # TODO: Handle force passed

    def render(self, source):
        return self.render_multitest(source)

    def render_multitest(self, multitest_report):
        return E.testsuites(
            *[self.render_testsuite(index, multitest_report, suite_report)
                for index, suite_report in enumerate(multitest_report)])

    def render_testsuite(self, index, multitest_report, testsuite_report):
        testcase_reports = []
        for child in testsuite_report:
            if isinstance(child, TestCaseReport):
                testcase_reports.append(child)
            elif isinstance(child, TestGroupReport) and\
                    child.category == Categories.PARAMETRIZATION:
                testcase_reports.extend(child.entries)
            else:
                raise TypeError('Unsupported report type: {}'.format(child))

        cases = [
            self.render_testcase(
                multitest_report,
                testsuite_report,
                testcase_report
            )
            for testcase_report in testcase_reports]

        # junit.xsd mandates system-out and system err
        cases.append(etree.Element("system-out"))
        cases.append(etree.Element("system-err"))

        return E.testsuite(
            *cases,
            hostname=socket.gethostname(),
            id=str(index),
            package='{}:{}'.format(
                multitest_report.name, testsuite_report.name),
            name=testsuite_report.name,
            errors=str(testsuite_report.counts.error),
            failures=str(testsuite_report.counts.failed),
            tests=str(len(testsuite_report))
        )

    def render_testcase(
        self, multitest_report, testsuite_report, testcase_report
    ):
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
                multitest_report.name,
                testsuite_report.name,
                testcase_report.name
            ),
            time=str(testcase_report.timer['run'].elapsed)
                if 'run' in testcase_report.timer else '0'
        )

    def render_testcase_errors(self, testcase_report):
        # This is retrieved from the log data created by report.logger
        return [
            E.error(message=log['message'])
            for log in testcase_report.logs if log['levelname'] == 'ERROR'
        ]

    def render_testcase_failures(self, testcase_report):

        # Depth does not matter, we just need entries in flat form
        flat_dicts = list(zip(*testcase_report.flattened_entries(depth=0)))[1]

        failed_assertions = [
            entry for entry in flat_dicts
            # Only get failing assertions
            if entry['meta_type'] == 'assertion' and
            not entry['passed'] and
            # Groups have no use in XML output
            not entry['type'] in ('Group', 'Summary')
        ]

        return [
            E.failure(
                message=entry['description'] or entry['type'],
                type='assertion'
            ) for entry in failed_assertions]


class XMLExporterConfig(ExporterConfig):
    """TODO"""

    def configuration_schema(self):
        overrides = Schema({
            ConfigOption('xml_dir', default=defaults.XML_DIR): str,
        })
        return self.inherit_schema(overrides, super(XMLExporterConfig, self))


class XMLExporter(Exporter):
    """
        Produces one XML file per each child of
        TestPlanReport (e.g. Multitest reports)
    """

    CONFIG = XMLExporterConfig

    # TODO: Add more renderers here when we support them (e.g. GTest etc)
    renderer_map = {
        Categories.MULTITEST: MultiTestRenderer,
    }

    def export(self, source):
        xml_dir = self.cfg.xml_dir

        if os.path.exists(xml_dir):
            shutil.rmtree(xml_dir)

        os.makedirs(xml_dir)

        files = set(os.listdir(xml_dir))

        for child_report in source:
            renderer = self.renderer_map[child_report.category]()
            element = etree.ElementTree(renderer.render(child_report))
            filename = '{}.xml'.format(slugify(child_report.name))
            filename = unique_name(filename, files)
            files.add(filename)

            file_path = os.path.join(self.cfg.xml_dir, filename)
            element.write(file_path, pretty_print=True)

        TESTPLAN_LOGGER.exporter_info(
            '%s XML files created at: %s', len(source), xml_dir)

