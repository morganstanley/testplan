"""Base classes for all Tests"""
import os
import sys
import subprocess
import six
import tempfile
import warnings

from lxml import objectify
from schema import Or, Use, And

from testplan.defaults import MAX_TEST_NAME_LENGTH
from testplan.common.config import ConfigOption, validate_func

from testplan.testing import filtering, ordering, tagging

from testplan.common.entity import (
    Resource,
    ResourceStatus,
    Runnable,
    RunnableResult,
    RunnableConfig,
)
from testplan.common.utils.process import subprocess_popen
from testplan.common.utils.timing import parse_duration, format_duration
from testplan.common.utils.process import enforce_timeout, kill_process
from testplan.common.utils.strings import slugify

from testplan.report import (
    test_styles,
    TestGroupReport,
    TestCaseReport,
    ReportCategories,
    RuntimeStatus,
)
from testplan.common.utils.logger import TESTPLAN_LOGGER
from testplan.testing.multitest.entries.assertions import RawAssertion
from testplan.testing.multitest.entries.base import Log


TEST_INST_INDENT = 2
SUITE_INDENT = 4
TESTCASE_INDENT = 6
ASSERTION_INDENT = 8


class TestConfig(RunnableConfig):
    """Configuration object for :py:class:`~testplan.testing.base.Test`."""

    @classmethod
    def get_options(cls):
        start_stop_signature = Or(
            None, validate_func("env"), validate_func("env", "result")
        )

        return {
            "name": And(str, lambda s: len(s) <= MAX_TEST_NAME_LENGTH),
            ConfigOption("description", default=None): Or(str, None),
            ConfigOption("environment", default=[]): [Resource],
            ConfigOption("before_start", default=None): start_stop_signature,
            ConfigOption("after_start", default=None): start_stop_signature,
            ConfigOption("before_stop", default=None): start_stop_signature,
            ConfigOption("after_stop", default=None): start_stop_signature,
            ConfigOption("test_filter"): filtering.BaseFilter,
            ConfigOption("test_sorter"): ordering.BaseSorter,
            ConfigOption("stdout_style"): test_styles.Style,
            ConfigOption("tags", default=None): Or(
                None, Use(tagging.validate_tag_value)
            ),
        }


class TestResult(RunnableResult):
    """
    Result object for
    :py:class:`~testplan.testing.base.Test` runnable
    test execution framework base class and all sub classes.

    Contains a test ``report`` object.
    """

    def __init__(self):
        super(TestResult, self).__init__()
        self.report = None


class Test(Runnable):
    """
    Base test instance class. Any runnable that runs a test
    can inherit from this class and override certain methods to
    customize functionality.

    :param name: Test instance name. Also used as uid.
    :type name: ``str``
    :param description: Description of test instance.
    :type description: ``str``
    :param environment: List of
        :py:class:`drivers <testplan.tesitng.multitest.driver.base.Driver>` to
        be started and made available on tests execution.
    :type environment: ``list``
    :param test_filter: Class with test filtering logic.
    :type test_filter: :py:class:`~testplan.testing.filtering.BaseFilter`
    :param test_sorter: Class with tests sorting logic.
    :type test_sorter: :py:class:`~testplan.testing.ordering.BaseSorter`
    :param before_start: Callable to execute before starting the environment.
    :type before_start: ``callable`` taking an environment argument.
    :param after_start: Callable to execute after starting the environment.
    :type after_start: ``callable`` taking an environment argument.
    :param before_stop: Callable to execute before stopping the environment.
    :type before_stop: ``callable`` taking environment and a result arguments.
    :param after_stop: Callable to execute after stopping the environment.
    :type after_stop: ``callable`` taking environment and a result arguments.
    :param stdout_style: Console output style.
    :type stdout_style: :py:class:`~testplan.report.testing.styles.Style`
    :param tags: User defined tag value.
    :type tags: ``string``, ``iterable`` of ``string``, or a ``dict`` with
        ``string`` keys and ``string`` or ``iterable`` of ``string`` as values.

    Also inherits all
    :py:class:`~testplan.common.entity.base.Runnable` options.
    """

    CONFIG = TestConfig
    RESULT = TestResult

    # Base test class only allows Test (top level) filtering
    filter_levels = [filtering.FilterLevel.TEST]

    def __init__(self, **options):
        super(Test, self).__init__(**options)

        if ":" in self.cfg.name:
            warnings.warn(
                "Multitest object contains colon in name: {}".format(
                    self.cfg.name
                )
            )

        for resource in self.cfg.environment:
            resource.parent = self
            resource.cfg.parent = self.cfg
            self.resources.add(resource)

        self._test_context = None
        self._init_test_report()

    def __str__(self):
        return "{}[{}]".format(self.__class__.__name__, self.name)

    def _new_test_report(self):
        return TestGroupReport(
            name=self.cfg.name,
            uid=self.cfg.name,
            description=self.cfg.description,
            category=self.__class__.__name__.lower(),
            tags=self.cfg.tags,
        )

    def _init_test_report(self):
        self.result.report = self._new_test_report()

    def get_tags_index(self):
        """
        Return the tag index that will be used for filtering.
        By default this is equal to the native tags for this object.

        However subclasses may build larger tag indices
        by collecting tags from their children for example.
        """
        return self.cfg.tags

    def get_filter_levels(self):
        if not self.filter_levels:
            raise ValueError(
                "`filter_levels` is not defined by {}".format(self)
            )
        return self.filter_levels

    @property
    def name(self):
        """Instance name. Also uid."""
        return self.cfg.name

    @property
    def description(self):
        return self.cfg.description

    @property
    def report(self):
        """Shortcut for the test report."""
        return self.result.report

    @property
    def stdout_style(self):
        """Stdout style input."""
        return self.cfg.stdout_style

    @property
    def test_context(self):
        if self._test_context is None:
            self._test_context = self.get_test_context()
        return self._test_context

    def get_test_context(self):
        raise NotImplementedError

    def get_stdout_style(self, passed):
        """Stdout style for status."""
        return self.stdout_style.get_style(passing=passed)

    def uid(self):
        """Instance name uid."""
        return self.cfg.name

    def should_run(self):
        return (
            self.cfg.test_filter.filter(
                test=self,
                # Instance level shallow filtering is applied by default
                suite=None,
                case=None,
            )
            and self.test_context
        )

    def should_log_test_result(self, depth, test_obj, style):
        """
        Return a tuple in which the first element indicates if need to log
        test results (Suite report, Testcase report, or result of assertions).
        The second one is the indent that should be kept at start of lines.
        """
        if isinstance(test_obj, TestGroupReport):
            if depth == 0:
                return style.display_test, TEST_INST_INDENT
            elif test_obj.category == "testsuite":
                return style.display_testsuite, SUITE_INDENT
            elif test_obj.category == "parametrization":
                return False, 0  # DO NOT display
            else:
                raise ValueError(
                    "Unexpected test group category: {}".format(
                        test_obj.category
                    )
                )
        elif isinstance(test_obj, TestCaseReport):
            return style.display_testcase, TESTCASE_INDENT
        elif isinstance(test_obj, dict):
            return style.display_assertion, ASSERTION_INDENT
        raise TypeError("Unsupported test object: {}".format(test_obj))

    def log_test_results(self, top_down=True):
        """
        Log test results. i.e. ProcessRunnerTest or PyTest

        :param top_down: Flag logging test results using a top-down approach
            or a bottom-up approach.
        :type top_down: ``bool``
        """
        report = self.result.report
        items = report.flatten(depths=True)
        entries = []  # Composed of (depth, report obj)

        def log_entry(depth, obj):
            name = obj["description"] if isinstance(obj, dict) else obj.name
            try:
                passed = obj["passed"] if isinstance(obj, dict) else obj.passed
            except KeyError:
                passed = True  # Some report entries (i.e. Log) always pass

            style = self.get_stdout_style(passed)
            display, indent = self.should_log_test_result(depth, obj, style)

            if display:
                if isinstance(obj, dict):
                    if obj["type"] == "RawAssertion":
                        header = obj["description"]
                        details = obj["content"]
                    elif "stdout_header" in obj and "stdout_details" in obj:
                        header = obj["stdout_header"]
                        details = obj["stdout_details"]
                    else:
                        return
                    if style.display_assertion:
                        TESTPLAN_LOGGER.test_info(indent * " " + header)
                    if details and style.display_assertion_detail:
                        details = os.linesep.join(
                            (indent + 2) * " " + line
                            for line in details.split(os.linesep)
                        )
                        TESTPLAN_LOGGER.test_info(details)
                else:
                    self.logger.log_test_status(
                        name, obj.status, indent=indent
                    )

        for depth, obj in items:
            if top_down:
                log_entry(depth, obj)
            else:
                while entries and depth <= entries[-1][0]:
                    log_entry(*(entries.pop()))
                entries.append((depth, obj))

        while entries:
            log_entry(*(entries.pop()))

    def propagate_tag_indices(self):
        """
        Basic step for propagating tag indices of the test report tree.
        This step may be necessary if the report tree is created
        in parts and then added up.
        """
        if len(self.report):
            self.report.propagate_tag_indices()

    def run_testcases_iter(self, testsuite_pattern="*", testcase_pattern="*"):
        """
        For a Test to be run interactively, it must implement this method.

        It is expected to run tests iteratively and yield a tuple containing
        a testcase report and the list of parent UIDs required to merge the
        testcase report into the main report tree.

        If it is not possible or very inefficient to run individual testcases
        in an iteratie manner, this method may instead run all the testcases
        in a batch and then return an iterator for the testcase reports and
        parent UIDs.

        :param testsuite_pattern: Filter pattern for testsuite level.
        :type testsuite_pattern: ``str``
        :param testcase_pattern: Filter pattern for testcase level.
        :type testsuite_pattern: ``str``
        :yield: generate tuples containing testcase reports and a list of the
            UIDs required to merge this into the main report tree, starting
            with the UID of this test.
        """
        raise NotImplementedError

    def start_test_resources(self):
        """
        Start all test resources but do not run any tests. Used in the
        interactive mode when environments may be started/stopped on demand.
        The base implementation is very simple but may be overridden in sub-
        classes to run additional setup pre- and post-environment start.
        """
        self.make_runpath_dirs()
        self.resources.start()

    def stop_test_resources(self):
        """
        Stop all test resources. As above, this method is used for the
        interactive mode and is very simple in this base Test class, but may
        be overridden by sub-classes.
        """
        self.resources.stop()

    def dry_run(self):
        """
        Return an empty report skeleton for this Test including all
        testsuites, testcases etc. hierarchy. Does not run any tests.
        """
        suites_to_run = self.test_context
        self.result.report = self._new_test_report()

        for testsuite, testcases in suites_to_run:
            testsuite_report = TestGroupReport(
                name=testsuite,
                category=ReportCategories.TESTSUITE,
                uid=testsuite,
            )

            for testcase in testcases:
                testcase_report = TestCaseReport(name=testcase, uid=testcase,)
                testsuite_report.append(testcase_report)

            self.result.report.append(testsuite_report)

        return self.result


class ProcessRunnerTestConfig(TestConfig):
    """
    Configuration object for
    :py:class:`~testplan.testing.base.ProcessRunnerTest`.
    """

    @classmethod
    def get_options(cls):
        return {
            "binary": str,
            ConfigOption("proc_env", default={}): dict,
            ConfigOption("proc_cwd", default=None): Or(str, None),
            ConfigOption("timeout", default=None): Or(
                None, float, int, Use(parse_duration)
            ),
            ConfigOption("ignore_exit_codes", default=[]): [int],
        }


class ProcessRunnerTest(Test):
    """
    A test runner that runs the tests in a separate subprocess.
    This is useful for running 3rd party testing
    frameworks (e.g. JUnit, GTest)

    Test report will be populated by parsing the generated report output file
    (report.xml file by default.)

    :param name: Test instance name. Also used as uid.
    :type name: ``str``
    :param binary: Path the to application binary or script.
    :type binary: ``str``
    :param description: Description of test instance.
    :type description: ``str``
    :param proc_env: Environment overrides for ``subprocess.Popen``.
    :type proc_env: ``dict``
    :param proc_cwd: Directory override for ``subprocess.Popen``.
    :type proc_cwd: ``str``
    :param timeout: Optional timeout for the subprocess. If a process
                    runs longer than this limit, it will be killed
                    and test will be marked as ``ERROR``.

                    String representations can be used as well as
                    duration in seconds. (e.g. 10, 2.3, '1m 30s', '1h 15m')

    :type timeout: ``str`` or ``number``
    :param ignore_exit_codes: When the test process exits with nonzero status
                    code, the test will be marked as ``ERROR``.
                    This can be disabled by providing a list of
                    numbers to ignore.
    :type ignore_exit_codes: ``list`` of ``int``

    Also inherits all
    :py:class:`~testplan.testing.base.Test` options.
    """

    CONFIG = ProcessRunnerTestConfig

    # Some process runners might not have a simple way to list
    # suites/testcases or might not even have the concept of test suites. If
    # no list_command is specified we will store all testcase results in a
    # single suite, with a default name.
    _DEFAULT_SUITE_NAME = "All Tests"

    def __init__(self, **options):
        super(ProcessRunnerTest, self).__init__(**options)

        self._test_context = None
        self._test_process = None  # will be set by `self.run_tests`
        self._test_process_retcode = None  # will be set by `self.run_tests`
        self._test_process_killed = False
        self._test_has_run = False

    @property
    def stderr(self):
        return os.path.join(self._runpath, "stderr")

    @property
    def stdout(self):
        return os.path.join(self._runpath, "stdout")

    @property
    def timeout_log(self):
        return os.path.join(self._runpath, "timeout.log")

    @property
    def report_path(self):
        return os.path.join(self._runpath, "report.xml")

    @property
    def test_context(self):
        if self._test_context is None:
            self._test_context = self.get_test_context()
        return self._test_context

    def test_command(self):
        """
        Override this to add extra options to the test command.

        :return: Command to run test process
        :rtype: ``list`` of ``str``
        """
        return [self.cfg.binary]

    def list_command(self):
        """
        Override this to generate the shell command that will cause the
        testing framework to list the tests available on stdout.

        :return: Command to list tests
        :rtype: ``list`` of ``str`` or ``NoneType``
        """
        return None

    def get_test_context(self):
        """
        Run the shell command generated by `list_command` in a subprocess,
        parse and return the stdout generated via `parse_test_context`.

        :return: Result returned by `parse_test_context`.
        :rtype: ``list`` of ``list``
        """
        cmd = self.list_command()  # pylint: disable=assignment-from-none
        if cmd is None:
            return [(self._DEFAULT_SUITE_NAME, ())]

        proc = subprocess_popen(
            cmd,
            cwd=self.cfg.proc_cwd,
            env=self.cfg.proc_env,
            stdout=subprocess.PIPE,
        )

        test_list_output = proc.communicate()[0]

        # with python3, stdout is bytes so need to decode.
        if not isinstance(test_list_output, six.string_types):
            test_list_output = test_list_output.decode(sys.stdout.encoding)

        return self.parse_test_context(test_list_output)

    def parse_test_context(self, test_list_output):
        """
        Override this to generate a nested list of test suite and test case
        context. Only required if `list_command` is overridden to return a
        command.

        The result will later on be used by test listers to generate the
        test context output for this test instance.

        Sample output:

        .. code-block:: python

          [
              ['SuiteAlpha', ['testcase_one', 'testcase_two'],
              ['SuiteBeta', ['testcase_one', 'testcase_two'],
          ]

        :param test_list_output: stdout from the list command
        :type test_list_output: bytes
        :return: Parsed test context from command line
                 output of the 3rd party testing library.
        :rtype: ``list`` of ``list``
        """
        raise NotImplementedError

    def timeout_callback(self):
        """
        Callback function that will be called by the daemon thread if
        a timeout occurs (e.g. process runs longer
        than specified timeout value).
        """

        self._test_process_killed = True
        with self.result.report.logged_exceptions():
            raise RuntimeError(
                "Timeout while running {instance} after {timeout}.".format(
                    instance=self, timeout=format_duration(self.cfg.timeout)
                )
            )

    def get_proc_env(self):
        self._json_ouput = os.path.join(self.runpath, "output.json")
        self.logger.debug("Json output: {}".format(self._json_ouput))
        env = {"JSON_REPORT": self._json_ouput}
        env.update(
            {key.upper(): val for key, val in self.cfg.proc_env.items()}
        )

        for driver in self.resources:
            driver_name = driver.uid()
            for attr in dir(driver):
                value = getattr(driver, attr)
                if attr.startswith("_") or callable(value):
                    continue
                env[
                    "DRIVER_{}_ATTR_{}".format(
                        slugify(driver_name).replace("-", "_"),
                        slugify(attr).replace("-", "_"),
                    ).upper()
                ] = str(value)

        return env

    def run_tests(self):
        """
        Run the tests in a subprocess, record stdout & stderr on runpath.
        Optionally enforce a timeout and log timeout related messages in
        the given timeout log path.
        """

        with self.result.report.logged_exceptions(), open(
            self.stderr, "w"
        ) as stderr, open(self.stdout, "w") as stdout:

            if not os.path.exists(self.cfg.binary):
                raise IOError(
                    "No runnable found at {} for {}".format(
                        self.cfg.binary, self
                    )
                )

            # Need to use the binary's absolute path if proc_cwd is specified,
            # otherwise won't be able to find the binary.
            if self.cfg.proc_cwd:
                self.cfg._options["binary"] = os.path.abspath(self.cfg.binary)

            test_cmd = self.test_command()

            self.result.report.logger.debug(
                "Running {} - Command: {}".format(self, test_cmd)
            )

            if not test_cmd:
                raise ValueError(
                    "Invalid test command generated for: {}".format(self)
                )

            self._test_process = subprocess_popen(
                test_cmd,
                stderr=stderr,
                stdout=stdout,
                cwd=self.cfg.proc_cwd,
                env=self.get_proc_env(),
            )

            if self.cfg.timeout:
                with open(self.timeout_log, "w") as timeout_log:
                    timeout_checker = enforce_timeout(
                        process=self._test_process,
                        timeout=self.cfg.timeout,
                        output=timeout_log,
                        callback=self.timeout_callback,
                    )
                    self._test_process_retcode = self._test_process.wait()
                    timeout_checker.join()
            else:
                self._test_process_retcode = self._test_process.wait()

            self._test_has_run = True

    def read_test_data(self):
        """
        Parse `report.xml` generated by the 3rd party testing tool and return
        the root node.

        You can override this if the test is generating a JSON file and you
        need custom logic to parse its contents for example.
\
        :return: Root node of parsed raw test data
        :rtype: ``xml.etree.Element``
        """
        with self.result.report.logged_exceptions(), open(
            self.report_path
        ) as report_file:
            return objectify.parse(report_file).getroot()

    def process_test_data(self, test_data):
        """
        Process raw test data that was collected and return a list of
        entries (e.g. TestGroupReport, TestCaseReport) that will be
        appended to the current test instance's report as children.

        :param test_data: Root node of parsed raw test data
        :type test_data: ``xml.etree.Element``
        :return: List of sub reports
        :rtype: ``list`` of ``TestGroupReport`` / ``TestCaseReport``
        """
        raise NotImplementedError

    def get_process_check_report(self, retcode, stdout, stderr):
        """
        When running a process fails (e.g. binary crash, timeout etc)
        we can still generate dummy testsuite / testcase reports with
        a certain hierarchy compatible with exporters and XUnit conventions.
        """
        assertion_content = "\n".join(
            [
                "Process: {}".format(self.cfg.binary),
                "Exit code: {}".format(retcode),
            ]
        )

        passed = retcode == 0 or retcode in self.cfg.ignore_exit_codes

        testcase_report = TestCaseReport(
            name="ExitCodeCheck",
            uid="ExitCodeCheck",
            suite_related=True,
            entries=[
                RawAssertion(
                    description="Process exit code check",
                    content=assertion_content,
                    passed=passed,
                ).serialize(),
                Log(
                    message=stdout.read(), description="Process stdout",
                ).serialize(),
                Log(
                    message=stderr.read(), description="Process stderr",
                ).serialize(),
            ],
        )

        testcase_report.runtime_status = RuntimeStatus.FINISHED

        suite_report = TestGroupReport(
            name="ProcessChecks",
            category=ReportCategories.TESTSUITE,
            entries=[testcase_report],
        )

        return suite_report

    def update_test_report(self):
        """
        Update current instance's test report with generated sub reports from
        raw test data. Skip report updates if the process was killed.
        """
        if self._test_process_killed or not self._test_has_run:
            with open(self.stdout) as stdout, open(self.stderr) as stderr:
                self.result.report.append(
                    self.get_process_check_report(
                        self._test_process_retcode, stdout, stderr,
                    )
                )
            return

        if len(self.result.report):
            raise ValueError(
                "Cannot update test report, "
                "it already has children: {}".format(self.result.report)
            )

        self.result.report.entries = self.process_test_data(
            test_data=self.read_test_data()
        )

        # Check process exit code as last step, as we don't want to create
        # an error log if the test report was populated
        # (with possible failures) already
        with open(self.stdout) as stdout, open(self.stderr) as stderr:
            self.result.report.append(
                self.get_process_check_report(
                    self._test_process_retcode, stdout, stderr,
                )
            )

    def pre_resource_steps(self):
        """Runnable steps to be executed before environment starts."""
        self._add_step(self.make_runpath_dirs)
        if self.cfg.before_start:
            self._add_step(self.cfg.before_start)

    def main_batch_steps(self):
        if self.cfg.after_start:
            self._add_step(self.cfg.after_start)
        self._add_step(self.run_tests)
        self._add_step(self.update_test_report)
        self._add_step(self.propagate_tag_indices)
        self._add_step(self.log_test_results, top_down=False)
        if self.cfg.before_stop:
            self._add_step(self.cfg.before_stop)

    def post_resource_steps(self):
        """Runnable steps to be executed after environment stops."""
        if self.cfg.after_stop:
            self._add_step(self.cfg.after_stop)

    def aborting(self):
        if self._test_process is not None:
            kill_process(self._test_process)
            self._test_process_killed = True

    def dry_run(self):
        """
        Return an empty report skeleton for this Test including all
        testsuites, testcases etc. hierarchy. Does not run any tests.
        """
        result = super(ProcessRunnerTest, self).dry_run()
        report = result.report

        testsuite_report = TestGroupReport(
            name="ProcessChecks",
            category=ReportCategories.TESTSUITE,
            uid="ProcessChecks",
        )

        testcase_report = TestCaseReport(
            name="ExitCodeCheck", uid="ExitCodeCheck", suite_related=True,
        )
        testsuite_report.append(testcase_report)
        report.append(testsuite_report)

        return result

    def run_testcases_iter(self, testsuite_pattern="*", testcase_pattern="*"):
        """
        Runs testcases as defined by the given filter patterns and yields
        testcase reports. A single testcase report is made for general checks
        of the test process, including checking the exit code and loggin stdout
        and stderr of the process. Then, testcase reports are generated from
        the output of the test process.

        For efficiency, we run all testcases in a single subprocess rather than
        running each testcase in a seperate process. This reduces the total
        time taken to run all testcases, however it will mean that testcase
        reports will not be generated until all testcases have finished
        running.

        :param testsuite_pattern: Filter pattern for testsuite level.
        :type testsuite_pattern: ``str``
        :param testcase_pattern: Filter pattern for testcase level.
        :type testsuite_pattern: ``str``
        :yield: generate tuples containing testcase reports and a list of the
            UIDs required to merge this into the main report tree, starting
            with the UID of this test.
        """
        self.make_runpath_dirs()
        test_cmd = self.test_command_filter(
            testsuite_pattern, testcase_pattern
        )
        self.logger.debug("test_cmd = %s", test_cmd)

        with tempfile.TemporaryFile(
            mode="w+"
        ) as stdout, tempfile.TemporaryFile(mode="w+") as stderr:
            exit_code = subprocess.call(
                test_cmd,
                stderr=stderr,
                stdout=stdout,
                cwd=self.cfg.proc_cwd,
                env=self.get_proc_env(),
            )

            stdout.seek(0)
            stderr.seek(0)
            check_report = self.get_process_check_report(
                exit_code, stdout, stderr
            )

        yield check_report["ExitCodeCheck"], [self.name, check_report.name]

        for suite_report in self.process_test_data(self.read_test_data()):
            for testcase_report in suite_report:
                yield testcase_report, [self.name, suite_report.name]

    def test_command_filter(self, testsuite_pattern, testcase_pattern):
        """
        Return the base test command with additional filtering to run a
        specific set of testcases. To be implemented by concrete subclasses.
        """
        raise NotImplementedError
