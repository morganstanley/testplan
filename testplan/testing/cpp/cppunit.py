import os

from schema import Or

from testplan.common.config import ConfigOption
from testplan.importers.cppunit import (
    CPPUnitImportedResult,
    CPPUnitResultImporter,
)
from testplan.testing.base import ProcessRunnerTest, ProcessRunnerTestConfig


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

    def _test_command(self):
        cmd = [self.resolved_bin]
        if self.cfg.filtering_flag and self.cfg.cppunit_filter:
            cmd.extend([self.cfg.filtering_flag, self.cfg.cppunit_filter])
        if self.cfg.file_output_flag:
            cmd.extend([self.cfg.file_output_flag, self.report_path])
        return cmd

    def _list_command(self):
        if self.cfg.listing_flag:
            return [self.resolved_bin, self.cfg.listing_flag]
        else:
            return super(Cppunit, self)._list_command()

    def read_test_data(self):

        importer = CPPUnitResultImporter(
            self.report_path if self.cfg.file_output_flag else self.stdout
        )
        return importer.import_result()

    def process_test_data(self, test_data: CPPUnitImportedResult):
        """
        XML output contains entries for skipped testcases
        as well, which are not included in the report.
        """

        return test_data.results()

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
            raise RuntimeError(
                "Cannot run individual test suite {}".format(testsuite_pattern)
            )

        if testcase_pattern not in ("*", self._VERIFICATION_TESTCASE_NAME):
            self.logger.user_info(
                'Should run testcases in pattern "%s", but cannot run'
                " individual testcases thus will run the whole test suite",
                testcase_pattern,
            )

        return self.test_command()

    def list_command_filter(self, testsuite_pattern, testcase_pattern):
        """
        Return the base list command with additional filtering to list a
        specific set of testcases.
        """
        return None  # Cppunit does not support listing by filter
