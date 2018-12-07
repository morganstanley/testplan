"""Base classes for all Tests"""
import os
import subprocess

from lxml import objectify
from schema import Or, Use, And

from testplan import defaults
from testplan.common.config import ConfigOption

from testplan.testing import filtering, ordering, tagging

from testplan.common.entity import Runnable, RunnableResult, RunnableConfig
from testplan.common.utils.process import subprocess_popen
from testplan.common.utils.timing import parse_duration, format_duration
from testplan.common.utils.process import enforce_timeout, kill_process

from testplan.report import test_styles, TestGroupReport, TestCaseReport, Status
from testplan.logger import TESTPLAN_LOGGER, get_test_status_message


class TestConfig(RunnableConfig):
    """Configuration object for :py:class:`~testplan.testing.base.Test`."""

    @classmethod
    def get_options(cls):
        return {
            # 'name': And(str, lambda s: s.count(' ') == 0),
            'name': str,
            ConfigOption('description', default=None): str,
            ConfigOption(
                'test_filter',
                default=filtering.Filter(),
                block_propagation=False
            ): filtering.BaseFilter,
            ConfigOption(
                'test_sorter',
                default=ordering.NoopSorter(),
                block_propagation=False
            ): ordering.BaseSorter,
            ConfigOption(
                'stdout_style',
                default=defaults.STDOUT_STYLE,
                block_propagation=False
            ): test_styles.Style,
            ConfigOption(
                'tags',
                default=None
            ): Or(None, Use(tagging.validate_tag_value)),
            ConfigOption(
                'part',
                default=None)
            : Or(None, And((int,), lambda tp:
                len(tp) == 2 and 0 <= tp[0] < tp[1] and tp[1] > 1))
        }


class TestResult(RunnableResult):
    """
    Result object for
    :py:class:`~testplan.testing.base.Test` runnable
    test execution framework base class and all sub classes.

    Contains a test ``report`` object.
    """

    def __init__(self):
        super(TestResult, self). __init__()
        self.report = None
        self.run = False


class Test(Runnable):
    """
    Base test instance class. Any runnable that runs a test
    can inherit from this class and override certain methods to
    customize functionality.

    :param name: Test instance name. Also used as uid.
    :type name: ``str``
    :param description: Description of test instance.
    :type description: ``str``
    :param test_filter: Class with test filtering logic.
    :type test_filter: :py:class:`~testplan.testing.filtering.BaseFilter`
    :param test_sorter: Class with tests sorting logic.
    :type test_sorter: :py:class:`~testplan.testing.ordering.BaseSorter`
    :param stdout_style: Console output style.
    :type stdout_style: :py:class:`~testplan.report.testing.styles.Style`

    Also inherits all
    :py:class:`~testplan.common.entity.base.Runnable` options.
    """

    CONFIG = TestConfig
    RESULT = TestResult

    # Base test class only allows Test (top level) filtering
    filter_levels = [filtering.FilterLevel.TEST]

    def __init__(self, **options):
        super(Test, self).__init__(**options)

        self._test_context = None
        self.result.report = TestGroupReport(
            name=self.cfg.name,
            description=self.cfg.description,
            category=self.__class__.__name__.lower(),
            uid=self.uid(),
            tags=self.cfg.tags,
            part=self.cfg.part,
        )

    def __str__(self):
        return '{}[{}]'.format(self.__class__.__name__, self.name)

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
                '`filter_levels` is not defined by {}'.format(self))
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
        return self.cfg.test_filter.filter(
            test=self,
            # Instance level shallow filtering is applied by default
            suite=None,
            case=None,
        ) and self.test_context

    def should_log_test_result(self, depth, test_obj, style):
        if isinstance(test_obj, TestGroupReport):
            if depth == 0:
                return style.display_test
            elif test_obj.category == 'suite':
                return style.display_suite
        elif isinstance(test_obj, TestCaseReport):
            return style.display_case
        elif isinstance(test_obj, dict) and test_obj['type'] == 'RawAssertion':
            return style.display_assertion
        raise TypeError('Unsupported test object: {}'.format(test_obj))

    def log_test_results(self):

        report = self.result.report
        items = report.flatten(depths=True)

        for depth, obj in items:
            name = obj['description'] if isinstance(obj, dict) else obj.name
            passed = obj['passed'] if isinstance(obj, dict) else obj.passed

            style = self.get_stdout_style(passed)

            if self.should_log_test_result(depth, obj, style):
                indent = (depth + 1) * 2 * ' '
                msg = get_test_status_message(
                    name=name,
                    passed=passed
                )
                if isinstance(obj, dict) and style.display_assertion_detail:
                    detail_indent = indent + (2 * ' ')
                    detail_str = os.linesep.join(
                        '{}{}'.format(detail_indent, line)
                        for line in obj['content'].splitlines())

                    msg = '{}{}{}'.format(msg, os.linesep, detail_str)

                TESTPLAN_LOGGER.test_info(
                    '{indent}{msg}'.format(
                        indent=indent,
                        msg=msg
                    )
                )

    def propagate_tag_indices(self):
        """
        Basic step for propagating tag indices of the test report tree.
        This step may be necessary if the report
        tree is created in parts and then added up.
        """
        if len(self.report):
            self.report.propagate_tag_indices()


class ProcessRunnerTestConfig(TestConfig):
    """
    Configuration object for
    :py:class:`~testplan.testing.base.ProcessRunnerTest`.
    """

    @classmethod
    def get_options(cls):
        return {
            'driver': str,
            ConfigOption('proc_env', default={}): dict,
            ConfigOption('proc_cwd', default=None): Or(str, None),
            ConfigOption('timeout', default=None): Or(
                float, int, Use(parse_duration)
            ),
            ConfigOption('ignore_exit_codes', default=[]): [int]
        }


class ProcessRunnerTest(Test):
    """
    A test runner that runs the tests in a separate subprocess.
    This is useful for running 3rd party testing
    frameworks (e.g. JUnit, GTest)

    Test report will be populated by parsing the generated report output file
    (report.xml file by default.)

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

    def __init__(self, **options):
        super(ProcessRunnerTest, self).__init__(**options)

        self._test_context = None
        self._test_process = None  # will be set by `self.run_tests`
        self._test_process_retcode = None  # will be set by `self.run_tests`
        self._test_process_killed = False
        self._test_has_run = False

    @property
    def stderr(self):
        return os.path.join(self._runpath, 'stderr')

    @property
    def stdout(self):
        return os.path.join(self._runpath, 'stdout')

    @property
    def timeout_log(self):
        return os.path.join(self._runpath, 'timeout.log')

    @property
    def report_path(self):
        return os.path.join(self._runpath, 'report.xml')

    @property
    def test_context(self):
        if self._test_context is None:
            self._test_context = self.get_test_context()
        return self._test_context

    def test_command(self):
        """
        Override this to generate the shell
        command that will run the test process.
        """
        return [self.cfg.driver]

    def list_command(self):
        """
        Override this to generate the shell command
        that will cause the testing framework to list the
        tests available on stdout.
        """
        raise NotImplementedError

    def get_test_context(self):
        """
        Run the shell command generated by `list_command` in a subprocess,
        parse and return the stdout generated via `parse_test_context`.

        :return: Result returned by `parse_test_context`.
        :rtype: ``list`` of ``list``
        """
        proc = subprocess_popen(
            self.list_command(),
            cwd=self.cfg.proc_cwd,
            env=self.cfg.proc_env,
            stdout=subprocess.PIPE)

        return self.parse_test_context(
            test_list_output=proc.communicate()[0])

    def parse_test_context(self, test_list_output):
        """
        Override this to generate a nested
        list of test suite and test case context.

        The result will later on be used by test listers to generate the
        test context output for this test instance.

        Sample output:

        [
            ['SuiteAlpha', ['testcase_one', 'testcase_two'],
            ['SuiteBeta', ['testcase_one', 'testcase_two'],
        ]

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
                'Timeout while running {instance} after {timeout}.'.format(
                    instance=self,
                    timeout=format_duration(self.cfg.timeout),
                ))

    def get_proc_env(self):
        self._json_ouput = os.path.join(self.runpath, 'output.json')
        self.logger.debug('Json output: {}'.format(self._json_ouput))
        env = {'JSON_REPORT': self._json_ouput}
        env.update(self.cfg.proc_env)
        return env

    def run_tests(self):
        """
        Run the tests in a subprocess, record stdout & stderr on runpath.
        Optionally enforce a timeout and log timeout related messages in
        the given timeout log path.
        """

        with self.result.report.logged_exceptions(), \
                open(self.stderr, 'w') as stderr, \
                open(self.stdout, 'w') as stdout:

            if not os.path.exists(self.cfg.driver):
                raise IOError('No runnable found at {} for {}'.format(
                    self.cfg.driver,
                    self
                ))

            # Need to use driver's absolute path if proc_cwd is specified,
            # otherwise won't be able to find the driver.
            if self.cfg.proc_cwd:
                self.cfg.driver = os.path.abspath(self.cfg.driver)

            test_cmd = self.test_command()

            self.result.report.logger.debug(
                'Running {} - Command: {}'.format(self, test_cmd))

            if not test_cmd:
                raise ValueError(
                    'Invalid test command generated for: {}'.format(self))

            self._test_process = subprocess_popen(
                self.test_command(),
                stderr=stderr,
                stdout=stdout,
                cwd=self.cfg.proc_cwd,
                env=self.get_proc_env(),
            )

            if self.cfg.timeout:
                with open(self.timeout_log, 'w') as timeout_log:
                    enforce_timeout(
                        process=self._test_process,
                        timeout=self.cfg.timeout,
                        output=timeout_log,
                        callback=self.timeout_callback
                    )
                    self._test_process_retcode = self._test_process.wait()
            else:
                self._test_process_retcode = self._test_process.wait()
            self._test_has_run = True

    def read_test_data(self):
        """
        Parse `report.xml` generated by the 3rd party testing tool and return
        the root node.

        You can override this if the test is generating a JSON file and you
        need custom logic to parse its contents for example.

        :return: Root node of parsed raw test data
        :rtype: ``xml.etree.Element``
        """
        with self.result.report.logged_exceptions(), \
                open(self.report_path) as report_file:
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

    def get_process_failure_report(self):
        """
        When running a process fails (e.g. binary crash, timeout etc)
        we can still generate dummy testsuite / testcase reports with
        a certain hierarchy compatible with exporters and XUnit conventions.
        """
        from testplan.testing.multitest.entries.assertions import RawAssertion

        assertion_content = os.linesep.join([
            'Process failure: {}'.format(self.cfg.driver),
            'Exit code: {}'.format(self._test_process_retcode),
            'stdout: {}'.format(self.stdout),
            'stderr: {}'.format(self.stderr)
        ])

        testcase_report = TestCaseReport(
            name='failure',
            entries=[
                RawAssertion(
                    description='Process failure details',
                    content=assertion_content,
                    passed=False
                ).serialize(),
            ]
        )

        testcase_report.status_override = Status.ERROR

        return TestGroupReport(
            name='ProcessFailure',
            category='suite',
            entries=[
                testcase_report
            ]
        )

    def update_test_report(self):
        """
        Update current instance's test report with generated sub reports from
        raw test data. Skip report updates if the process was killed.
        """
        if self._test_process_killed or not self._test_has_run:
            self.result.report.append(self.get_process_failure_report())
            return

        if len(self.result.report):
            raise ValueError(
                'Cannot update test report,'
                ' it already has children: {}'.format(self.result.report))

        self.result.report.entries = self.process_test_data(
            test_data=self.read_test_data()
        )

        retcode = self._test_process_retcode

        # Check process exit code as last step, as we don't want to create
        # an error log if the test report was populated
        # (with possible failures) already

        if retcode != 0\
                and retcode not in self.cfg.ignore_exit_codes\
                and not len(self.result.report):
            with self.result.report.logged_exceptions():
                self.result.report.append(self.get_process_failure_report())

    def pre_resource_steps(self):
        """Runnable steps to be executed before environment starts."""
        self._add_step(self.make_runpath_dirs)

    def main_batch_steps(self):
        self._add_step(self.run_tests)
        self._add_step(self.update_test_report)
        self._add_step(self.propagate_tag_indices)
        self._add_step(self.log_test_results)

    def aborting(self):
        kill_process(self._test_process)
        self._test_process_killed = True
