from schema import Or

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


class GTestConfig(ProcessRunnerTestConfig):
    """
    Configuration object for
    :py:class:`~testplan.testing.cpp.gtest.GTest`.
    """

    @classmethod
    def get_options(cls):
        # `gtest_output` is implicitly overridden to generate xml output
        # on the test instance's runpath.

        # `gtest_color` is not supported as we produce Testplan style output via
        # parsed test results.

        # `gtest_catch_exceptions` and `gtest_break_on_failure` are not
        # supported as running GTest with a debugger
        # is not possible within Testplan.

        return {
            ConfigOption("gtest_filter", default=""): str,
            ConfigOption("gtest_also_run_disabled_tests", default=False): bool,
            # Originally Google Test allows negative values, causing test to
            # be repeated indefinitely, which would always cause a timeout
            # error within Testplan context, so we
            # only allow non-negative values.
            ConfigOption("gtest_repeat", default=1): int,
            ConfigOption("gtest_shuffle", default=False): bool,
            ConfigOption("gtest_random_seed", default=0): int,
            ConfigOption("gtest_stream_result_to", default=""): str,
            ConfigOption("gtest_death_test_style", default="fast"): Or(
                "fast", "threadsafe"
            ),
        }


class GTest(ProcessRunnerTest):
    """
    Subprocess test runner for Google Test: https://github.com/google/googletest

    For original docs please see:

    https://github.com/google/googletest/blob/master/googletest/docs/AdvancedGuide.md
    https://github.com/google/googletest/blob/master/googletest/docs/FAQ.md

    Most of the configuratin options of GTest are
    just simple wrappers for native arguments.

    :param name: Test instance name, often used as uid of test entity.
    :type name: ``str``
    :param binary: Path to the application binary or script.
    :type binary: ``str``
    :param description: Description of test instance.
    :type description: ``str``
    :param gtest_filter: Native test filter pattern that will be
                        used by GTest internally.
    :type gtest_filter: ``str``
    :param gtest_also_run_disabled_tests: Will run disabled tests
                                        as well when set to ``True``.
    :type gtest_also_run_disabled_tests: ``bool``
    :param gtest_repeat: Repeats the GTest multiple times. Only allows
                    nonzero values, otherwise Testplan would stop
                    the test execution due to timeout.
    :type gtest_repeat: ``int``
    :param gtest_shuffle: Will run the tests in random
                        order when set to ``True``.
    :type gtest_shuffle: ``bool``
    :param gtest_random_seed: Integer that can be used
                            for the shuffling operation.
    :type gtest_random_seed: ``int``
    :param gtest_stream_result_to: Flag for specifying host name and port number
                                on which to stream test results.
    :type gtest_stream_result_to: ``str``
    :param gtest_death_test_style: Test style flag, can either be
                        ``threadsafe`` or ``fast``. (Default value is ``fast``)
    :type gtest_death_test_style: ``str``

    Also inherits all
    :py:class:`~testplan.testing.base.ProcessRunnerTest` options.
    """

    CONFIG = GTestConfig

    def __init__(
        self,
        name,
        binary,
        description=None,
        gtest_filter="",
        gtest_also_run_disabled_tests=False,
        gtest_repeat=1,
        gtest_shuffle=False,
        gtest_random_seed=0,
        gtest_stream_result_to="",
        gtest_death_test_style="fast",
        **options
    ):
        options.update(self.filter_locals(locals()))
        super(GTest, self).__init__(**options)

    def base_command(self):
        cmd = [self.cfg.binary]
        if self.cfg.gtest_filter:
            cmd.append("--gtest_filter={}".format(self.cfg.gtest_filter))
        return cmd

    def test_command(self):
        cmd = self.base_command() + [
            "--gtest_output=xml:{}".format(self.report_path),
            "--gtest_death_test_style={}".format(
                self.cfg.gtest_death_test_style
            ),
        ]

        if self.cfg.gtest_also_run_disabled_tests:
            cmd.append("--gtest_also_run_disabled_tests")
        if self.cfg.gtest_repeat > 1:
            cmd.append("--gtest_repeat={}".format(self.cfg.gtest_repeat))

        # TODO: Add integration with ShuffleSorter
        if self.cfg.gtest_shuffle:
            cmd.append("--gtest_shuffle")
            if self.cfg.gtest_random_seed:
                cmd.append(
                    "--gtest_random_seed={}".format(self.cfg.gtest_random_seed)
                )

        if self.cfg.gtest_stream_result_to:
            cmd.append(
                "--gtest_stream_result_to={}".format(
                    self.cfg.gtest_stream_result_to
                )
            )

        return cmd

    def list_command(self):
        return self.base_command() + ["--gtest_list_tests"]

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
            suite_has_run = False

            for testcase in suite.getchildren():

                testcase_name = testcase.attrib["name"]
                testcase_report = TestCaseReport(
                    name=testcase_name, uid=testcase_name
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
                            passed=entry.tag != "failure",
                        )
                        testcase_report.append(
                            registry.serialize(assertion_obj)
                        )

                testcase_report.runtime_status = RuntimeStatus.FINISHED

                if testcase.attrib["status"] != "notrun":
                    suite_report.append(testcase_report)
                    suite_has_run = True

            if suite_has_run:
                result.append(suite_report)

        return result

    def parse_test_context(self, test_list_output):
        """Parse GTest test listing from stdout"""
        # Sample Test Declaration:
        #
        #     TEST(SquareRootTest, PositiveNos) {
        #         ...
        #     }
        #
        #     TEST(SquareRootTest, NegativeNos) {
        #         ...
        #     }
        #
        #     TEST(SquareRootTestNonFatal, PositiveNos) {
        #         ...
        #     }
        #
        #     TEST(SquareRootTestNonFatal, NegativeNos) {
        #         ...
        #     }
        #
        # Sample command line output:
        #
        #     SquareRootTest.
        #       PositiveNos
        #       NegativeNos
        #     SquareRootTestNonFatal.
        #       PositiveNos
        #       NegativeNos
        #
        #
        # Sample Result:
        #
        # [
        #     ['SquareRootTest', ['PositiveNos', 'NegativeNos']],
        #     ['SquareRootTestNonFatal', ['PositiveNos', 'NegativeNos']],
        # ]
        result = []
        for line in test_list_output.splitlines():
            if line.endswith("."):
                result.append([line[:-1], []])
            else:
                result[-1][1].append(line.strip())
        return result

    def update_test_report(self):
        """
        Attach XML report contents to the report, which can be
        used by XML exporters, but will be discarded by serializers.
        """
        super(GTest, self).update_test_report()

        with open(self.report_path) as report_xml:
            self.result.report.xml_string = report_xml.read()

    def test_command_filter(self, testsuite_pattern, testcase_pattern):
        """
        Return the base test command with additional filtering to run a
        specific set of testcases.
        """
        cmd = self.test_command()
        if testsuite_pattern != "*" or testcase_pattern != "*":
            cmd.append(
                "--gtest_filter={}.{}".format(
                    testsuite_pattern, testcase_pattern
                )
            )
        return cmd
