from schema import Or

from testplan.common.config import ConfigOption

from ..base import ProcessRunnerTest, ProcessRunnerTestConfig
from ...importers.gtest import GTestResultImporter


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

    Most of the configuration options of GTest are
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
        cmd = [self.resolved_bin]
        if self.cfg.gtest_filter:
            cmd.append("--gtest_filter={}".format(self.cfg.gtest_filter))
        return cmd

    def _test_command(self):
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

    def _list_command(self):
        return self.base_command() + ["--gtest_list_tests"]

    def read_test_data(self):
        importer = GTestResultImporter(self.report_path)
        return importer.import_result()

    def process_test_data(self, test_data):
        return test_data.results()

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
        # SquareRootTest.
        #   PositiveNos
        #   NegativeNos
        # SquareRootTestNonFatal.
        #   PositiveNos
        #   NegativeNos
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
        super(GTest, self).update_test_report()

        try:
            with open(self.report_path) as report_xml:
                self.result.report.xml_string = report_xml.read()
        except Exception:
            self.result.report.xml_string = ""

    def test_command_filter(self, testsuite_pattern, testcase_pattern):
        """
        Return the base test command with additional filtering to run a
        specific set of testcases.
        """
        cmd = self.test_command()

        if testsuite_pattern == self._VERIFICATION_SUITE_NAME:
            testsuite_pattern = "*"
            if testcase_pattern == self._VERIFICATION_TESTCASE_NAME:
                testcase_pattern = "*"
        if testsuite_pattern != "*" or testcase_pattern != "*":
            cmd.append(
                "--gtest_filter={}.{}".format(
                    testsuite_pattern, testcase_pattern
                )
            )

        return cmd

    def list_command_filter(self, testsuite_pattern, testcase_pattern):
        """
        Return the base list command with additional filtering to list a
        specific set of testcases.
        """
        cmd = self.list_command()
        if testsuite_pattern == self._VERIFICATION_SUITE_NAME:
            testsuite_pattern = "*"
            if testcase_pattern == self._VERIFICATION_TESTCASE_NAME:
                testcase_pattern = "*"
        if testsuite_pattern != "*" or testcase_pattern != "*":
            cmd.append(
                "--gtest_filter={}.{}".format(
                    testsuite_pattern, testcase_pattern
                )
            )
        return cmd
