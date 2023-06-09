"""PyTest test runner."""
import collections
import inspect
import os
import re
import traceback
from typing import Dict, Generator

import pytest
from schema import Or

from testplan.common.config import ConfigOption
from testplan.common.utils import validation
from testplan.report import (
    ReportCategories,
    RuntimeStatus,
    Status,
    TestCaseReport,
    TestGroupReport,
)
from testplan.testing import base as testing
from testplan.testing.multitest.entries import assertions
from testplan.testing.multitest.entries import base as entries_base
from testplan.testing.multitest.entries.schemas.base import (
    registry as schema_registry,
)
from testplan.testing.multitest.entries.stdout.base import (
    registry as stdout_registry,
)
from testplan.testing.multitest.result import Result as MultiTestResult

# Regex for parsing suite and case name and case parameters
_CASE_REGEX = re.compile(
    r"^(?P<suite_name>.+)::"
    r"(?P<case_name>[^\[]+)(?:\[(?P<case_params>.+)\])?$",
    re.DOTALL,
)


class PyTestConfig(testing.TestConfig):
    """
    Configuration object for
    :py:class:`~testplan.testing.py_test.PyTest` test runner.
    """

    @classmethod
    def get_options(cls):
        return {
            "target": Or(str, [str]),
            ConfigOption("select", default=""): str,
            ConfigOption("extra_args", default=None): Or([str], None),
            ConfigOption(
                "result", default=MultiTestResult
            ): validation.is_subclass(MultiTestResult),
        }


class PyTest(testing.Test):
    """
    PyTest plugin for Testplan. Allows tests written for PyTest to be run from
    Testplan, with the test results logged and included in the Testplan report.

    :param name: Test instance name, often used as uid of test entity.
    :type name: ``str``
    :param target: Target of PyTest configuration.
    :type target: ``str`` or ``list`` of ``str``
    :param description: Description of test instance.
    :type description: ``str``
    :param select: Selection of PyTest configuration.
    :type select: ``str``
    :param extra_args: Extra arguments passed to pytest.
    :type extra_args: ``NoneType`` or ``list`` of ``str``
    :param result: Result that contains assertion entries.
    :type result: :py:class:`~testplan.testing.multitest.result.Result`

    Also inherits all :py:class:`~testplan.testing.base.Test` options.
    """

    CONFIG = PyTestConfig

    def __init__(
        self,
        name,
        target,
        description=None,
        select="",
        extra_args=None,
        result=MultiTestResult,
        **options
    ):
        options.update(self.filter_locals(locals()))
        super(PyTest, self).__init__(**options)

        # Initialise a seperate plugin object to pass to PyTest. This avoids
        # namespace clashes with the PyTest object, since PyTest will scan for
        # methods that look like hooks in the plugin.
        quiet = not self._debug_logging_enabled
        self._pytest_plugin = _ReportPlugin(self, self.report, quiet)
        self._collect_plugin = _CollectPlugin(quiet)
        self._pytest_args = self._build_pytest_args()

        # Map from testsuite/testcase name to nodeid. Filled out after
        # tests are collected via dry_run().
        self._nodeids = None

    def main_batch_steps(self):
        """Specify the test steps: run the tests, then log the results."""
        self._add_step(self.run_tests)
        self._add_step(self.log_test_results, top_down=False)

    def setup(self):
        """Setup the PyTest plugin for the suite."""
        self._pytest_plugin.setup()

    def run_tests(self):
        """Run pytest and wait for it to terminate."""
        # Execute pytest with self as a plugin for hook support
        with self.report.timer.record("run"):
            return_code = pytest.main(
                self._pytest_args, plugins=[self._pytest_plugin]
            )

            if return_code == 5:
                self.result.report.status_override = Status.UNSTABLE
                self.logger.info("No tests were run")
            elif return_code != 0:
                self.result.report.status_override = Status.FAILED
                self.logger.info(
                    "pytest exited with return code %d", return_code
                )

    def _collect_tests(self):
        """Collect test items but do not run any."""

        # We shall restore sys.path after calling pytest.main
        # as it might prepend test rootdir in sys.path
        # but this has other problem (helper package)
        return_code = pytest.main(
            self._pytest_args + ["--collect-only"],
            plugins=[self._collect_plugin],
        )

        if return_code not in (0, 5):  # rc 5: no tests were run
            raise RuntimeError(
                "Collection failure, exit code = {}".format(return_code)
            )

        return self._collect_plugin.collected

    def get_test_context(self):
        """
        Inspect the test suites and cases by running PyTest with the
        --collect-only flag and passing in our collection plugin.

        :return: List containing pairs of suite name and testcase names.
        :rtype: List[Tuple[str, List[str]]]
        """
        try:
            collected = self._collect_tests()
        except RuntimeError:
            self.result.report.status_override = Status.ERROR
            self.logger.exception("Failed to collect tests.")
            return []

        # The plugin will handle converting PyTest tests into suites and
        # testcase names.
        suites = collections.defaultdict(set)
        for item in collected:
            suite_name, case_name, _ = _case_parse(item.nodeid)
            suites[suite_name].add(case_name)

        return [
            (suite, list(testcases)) for suite, testcases in suites.items()
        ]

    def dry_run(self):
        """
        Collect tests and build a report tree skeleton, but do not run any
        tests.
        """
        self.result.report = self._new_test_report()
        self._nodeids = {
            "testsuites": {},
            "testcases": collections.defaultdict(dict),
        }

        for item in self._collect_tests():
            _add_empty_testcase_report(item, self.result.report, self._nodeids)

        return self.result

    def run_testcases_iter(
        self,
        testsuite_pattern: str = "*",
        testcase_pattern: str = "*",
        shallow_report: Dict = None,
    ) -> Generator:
        """
        Run all testcases and yield testcase reports.

        :param testsuite_pattern: pattern to match for testsuite names
        :param testcase_pattern: pattern to match for testcase names
        :param shallow_report: shallow report entry
        :return: generator yielding testcase reports and UIDs for merge step
        """
        if not self._nodeids:
            # Need to collect the tests so we know the nodeids for each
            # testsuite/case.
            self.dry_run()

        test_report = self._new_test_report()
        quiet = not self._debug_logging_enabled
        pytest_plugin = _ReportPlugin(self, test_report, quiet)
        pytest_plugin.setup()

        pytest_args, current_uids = self._build_iter_pytest_args(
            testsuite_pattern, testcase_pattern
        )
        # Will call `pytest.main` to run all testcases as a whole, accordingly,
        # runtime status of all these testcases will be set at the same time.
        yield {"runtime_status": RuntimeStatus.RUNNING}, current_uids

        self.logger.info("Running PyTest with args: %r", pytest_args)
        return_code = pytest.main(pytest_args, plugins=[pytest_plugin])
        self.logger.info("PyTest exit code: %d", return_code)

        for suite_report in test_report:
            for child_report in suite_report:
                if isinstance(child_report, TestCaseReport):
                    yield (
                        child_report,
                        [test_report.uid, suite_report.uid],
                    )
                elif isinstance(child_report, TestGroupReport):
                    if (
                        child_report.category
                        != ReportCategories.PARAMETRIZATION
                    ):
                        raise RuntimeError(
                            "Unexpected report category: {}".format(
                                child_report.category
                            )
                        )

                    for testcase_report in child_report:
                        yield (
                            testcase_report,
                            [
                                test_report.uid,
                                suite_report.uid,
                                child_report.uid,
                            ],
                        )
                else:
                    raise TypeError(
                        "Unexpected report type: {}".format(type(child_report))
                    )

    def _build_iter_pytest_args(self, testsuite_pattern, testcase_pattern):
        """
        Build the PyTest args for running a particular set of testsuites and
        testcases as specified.
        """
        if self._nodeids is None:
            raise RuntimeError("Need to call dry_run() first")

        if testsuite_pattern == "*" and testcase_pattern == "*":
            if isinstance(self.cfg.target, str):
                pytest_args = [self.cfg.target]
            else:
                pytest_args = self.cfg.target[:]
            current_uids = [self.uid()]
        elif testcase_pattern == "*":
            pytest_args = [self._nodeids["testsuites"][testsuite_pattern]]
            current_uids = [self.uid(), testsuite_pattern]
        else:
            pytest_args = [
                self._nodeids["testcases"][testsuite_pattern][testcase_pattern]
            ]
            suite_name, case_name, case_params = _case_parse(pytest_args[0])
            if case_params:
                current_uids = [
                    self.uid(),
                    suite_name,
                    case_name,
                    "{}[{}]".format(case_name, case_params),
                ]
            else:
                current_uids = [self.uid(), suite_name, case_name]

        if self.cfg.extra_args:
            pytest_args.extend(self.cfg.extra_args)

        return pytest_args, current_uids

    def _build_pytest_args(self):
        """
        :return: a list of the args to be passed to PyTest
        :rtype: List[str]
        """
        if isinstance(self.cfg.target, str):
            pytest_args = [self.cfg.target]
        else:
            pytest_args = self.cfg.target[:]

        if self.cfg.select:
            pytest_args.extend(["-k", self.cfg.select])

        if self.cfg.extra_args:
            pytest_args.extend(self.cfg.extra_args)

        return pytest_args


class _ReportPlugin:
    """
    Plugin object passed to PyTest. Contains hooks used to update the Testplan
    report with the status of testcases.
    """

    def __init__(self, parent, report, quiet):
        self._parent = parent
        self._report = report
        self._quiet = quiet

        # Collection of suite reports - will be initialised by the setup()
        # method.
        self._suite_reports = None

        # The current working testcase report. It needs to be stored on this
        # object since it is set and read by different callback hooks.
        self._current_case_report = None

        # Result object which supports various assertions like in MultiTest.
        # Its entries will later be added to current testcase report.
        self._current_result_obj = None

        # Create fixture function for interface
        self._fixtures_init()

    def _fixtures_init(self):
        """
        Register fixtures with pytest.
        """

        @pytest.fixture
        def result():
            """
            Return the result object for the current test case.

            :return: the result object for the current test case
            :rtype: ``Result``
            """
            return self._current_result_obj

        @pytest.fixture
        def env():
            """
            Return the testing environment.

            :return: the testing environment
            :rtype: ``Environment``
            """
            return self._parent.resources

        # PyTest picks up fixtures from all files it loads (including plugins)
        self.result = result
        self.env = env

    def setup(self):
        """Set up environment as required."""
        self._suite_reports = collections.defaultdict(collections.OrderedDict)

    def case_report(self, suite_name, case_name, case_params):
        """
        Return the case report for the specified suite and case name, creating
        it first if necessary.

        :param suite_name: the suite name to get the report for
        :type suite_name: ``str``
        :param case_name: the case name to get the report for
        :type case_name: ``str``
        :param case_params: the case parameters to get the report for
        :type case_params: ``str`` or ``NoneType``
        :return: the case report
        :rtype: :py:class:`testplan.report.testing.TestCaseReport`
        """
        if case_params is None:
            report = self._suite_reports[suite_name].get(case_name)
            if report is None:
                report = TestCaseReport(case_name, uid=case_name)
                self._suite_reports[suite_name][case_name] = report
            return report

        else:
            group_report = self._suite_reports[suite_name].get(case_name)
            if group_report is None:
                # create group report for parametrized testcases
                group_report = TestGroupReport(
                    name=case_name,
                    uid=case_name,
                    category=ReportCategories.PARAMETRIZATION,
                )
                self._suite_reports[suite_name][case_name] = group_report

            case_name = "{}[{}]".format(case_name, case_params)
            try:
                report = group_report.get_by_uid(case_name)
            except:
                # create report of parametrized testcase
                report = TestCaseReport(name=case_name, uid=case_name)
                group_report.append(report)
            return report

    def pytest_runtest_setup(self, item):
        """
        Hook called by pytest to set up a test.

        :param item: the test item to set up (see pytest documentation)
        """
        # Extract suite name, case name and parameters
        suite_name, case_name, case_params = _case_parse(item.nodeid)
        report = self.case_report(suite_name, case_name, case_params)

        try:
            func_doc = item.function.__doc__
        except AttributeError:
            func_doc = None

        if func_doc is not None:
            report.description = os.linesep.join(
                "    {}".format(line)
                for line in inspect.getdoc(item.function).split(os.linesep)
            )

        self._current_case_report = report
        self._current_result_obj = self._parent.cfg.result(
            stdout_style=self._parent.stdout_style,
            _scratch=self._parent.scratch,
        )

    def pytest_runtest_teardown(self, item):
        """
        Hook called by pytest to tear down a test.

        :param item: the test item to tear down (see pytest documentation)
        """
        self._current_case_report = None
        self._current_result_obj = None

    def pytest_runtest_logreport(self, report):
        """
        Hook called by pytest to report on the result of a test.

        :param report: the test report for the item just tested (see pytest
                       documentation)
        """
        if report.when == "setup":
            if report.skipped:
                if self._current_case_report is None:
                    suite_name, case_name, case_params = _case_parse(
                        report.nodeid
                    )
                    testcase_report = self.case_report(
                        suite_name, case_name, case_params
                    )
                else:
                    testcase_report = self._current_case_report

                # Status set to be SKIPPED if testcase is marked skip or xfail
                # lower versioned PyTest does not support this feature
                testcase_report.status_override = Status.SKIPPED

        elif report.when == "call":
            if self._current_case_report is None:
                raise RuntimeError(
                    "Cannot store testcase results to report: no report "
                    "object was created."
                )

            if self._current_result_obj.entries:
                # Add the assertion entry to the case report
                for entry in self._current_result_obj.entries:
                    stdout_renderer = stdout_registry[entry]()
                    stdout_header = stdout_renderer.get_header(entry)
                    stdout_details = stdout_renderer.get_details(entry) or ""

                    # Add 'stdout_header' and 'stdout_details' attributes to
                    # serialized entries for standard output later
                    serialized_entry = schema_registry.serialize(entry)
                    serialized_entry.update(
                        stdout_header=stdout_header,
                        stdout_details=stdout_details,
                    )
                    self._current_case_report.append(serialized_entry)

                self._current_case_report.attachments.extend(
                    self._current_result_obj.attachments
                )

            if report.failed:
                self._current_case_report.status_override = Status.FAILED
            else:
                self._current_case_report.pass_if_empty()
            self._current_case_report.runtime_status = RuntimeStatus.FINISHED

        elif report.when == "teardown":
            pass

    def pytest_exception_interact(self, node, call, report):
        """
        Hook called when an exception raised and it can be handled. This hook
        is only called if the exception is not an PyTest internal exception.

        :param node: PyTest Function or Module object
        :param call: PyTest CallInfo object
        :param report: PyTest TestReport or CollectReport object
        """
        if call.when in ("memocollect", "collect"):
            # Failed to collect tests: log to console and mark the report as
            # ERROR.
            self._report.logger.error(
                "".join(
                    traceback.format_exception(
                        call.excinfo.type, call.excinfo.value, call.excinfo.tb
                    )
                )
            )
            self._report.status_override = Status.ERROR

        elif self._current_case_report is not None:
            # Log assertion errors or exceptions in testcase report
            trace = call.excinfo.traceback[-1]
            message = (
                getattr(call.excinfo.value, "message", None)
                or getattr(call.excinfo.value, "msg", None)
                or getattr(call.excinfo.value, "args", None)
                or ""
            )
            if isinstance(message, (tuple, list)):
                message = message[0]

            header = (
                (
                    "Assertion - Fail"
                    if call.excinfo.typename == "AssertionError"
                    else "Exception raised"
                )
                if call.when == "call"
                else "{} - Fail".format(call.when)
            )
            details = (
                "File: {}\nLine: {}\n{}: {}".format(
                    str(trace.path),
                    trace.lineno + 1,
                    call.excinfo.typename,
                    message,
                )
                if call.excinfo.typename == "AssertionError"
                else (
                    report.longreprtext
                    if hasattr(report, "longreprtext")
                    else str(report.longrepr)
                )
            )

            assertion_obj = assertions.RawAssertion(
                description=header, content=details, passed=False
            )
            serialized_obj = schema_registry.serialize(assertion_obj)
            self._current_case_report.append(serialized_obj)
            self._current_case_report.status_override = Status.FAILED

            for capture, description in (
                ("caplog", "Captured Log"),
                ("capstdout", "Captured Stdout"),
                ("capstderr", "Captured Stderr"),
            ):
                message = getattr(report, capture)
                if message:
                    assertion_obj = entries_base.Log(
                        message, description=description
                    )
                    serialized_obj = schema_registry.serialize(assertion_obj)
                    self._current_case_report.append(serialized_obj)

        else:
            self._report.logger.error(
                "Exception occured outside of a testcase: during %s", call.when
            )
            self._report.logger.error(
                "".join(
                    traceback.format_exception(
                        call.excinfo.type, call.excinfo.value, call.excinfo.tb
                    )
                )
            )

    @pytest.hookimpl(trylast=True)
    def pytest_configure(self, config):
        """
        Hook called by pytest upon startup. Disable output to terminal.

        :param config: pytest config object
        """
        if self._quiet:
            config.pluginmanager.unregister(name="terminalreporter")

    def pytest_unconfigure(self, config):
        """
        Hook called by pytest before exiting. Collate suite reports.

        :param config: pytest config object
        """
        # Collate suite reports
        for suite_name, cases in self._suite_reports.items():
            suite_report = TestGroupReport(
                name=suite_name,
                uid=suite_name,
                category=ReportCategories.TESTSUITE,
            )

            for case in cases.values():
                suite_report.append(case)

            self._report.append(suite_report)


class _CollectPlugin:
    """
    PyTest plugin used when collecting tests. Provides access to the collected
    test suites and testcases via the `collected` property.
    """

    def __init__(self, quiet):
        self._quiet = quiet
        self.collected = None

    @pytest.hookimpl(trylast=True)
    def pytest_configure(self, config):
        """
        Hook called by pytest upon startup. Disable output to terminal.

        :param config: pytest config object
        """
        if self._quiet:
            config.pluginmanager.unregister(name="terminalreporter")

    def pytest_collection_finish(self, session):
        """
        PyTest hook, called after collection is finished.
        """
        self.collected = session.items


def _case_parse(nodeid):
    """
    Parse a nodeid into a shorterned URL-safe suite name, case name, and case
    parameters.

    :param nodeid: the test nodeid
    :type nodeid: ``str``
    :raises ValueError: if nodeid is invalid
    :return: a tuple consisting of (suite name, case name, case parameters)
    :rtype: ``tuple``
    """
    suite_name, case_name, case_params = _split_nodeid(nodeid)
    return (_short_suite_name(suite_name), case_name, case_params)


def _split_nodeid(nodeid):
    """
    Split a nodeid into its full suite name, case name, and case parameters.

    :param nodeid: the test nodeid
    :type nodeid: ``str``
    :raises ValueError: if nodeid is invalid
    :return: a tuple consisting of (suite name, case name, case parameters)
    :rtype: ``tuple``
    """
    match = _CASE_REGEX.match(nodeid.replace("::()::", "::"))

    if match is None:
        raise ValueError("Invalid nodeid")

    suite_name, case_name, case_params = match.groups()

    return suite_name, case_name, case_params


def _short_suite_name(suite_name):
    """
    Remove any path elements or .py extensions from the suite name.
    E.g. "tests/my_test.py" -> "my_test"
    Note that even on Windows, PyTest stores path elements separated by "/"
    which is why we don't split on os.sep here.
    """
    return os.path.basename(suite_name)


def _add_empty_testcase_report(item, test_report, nodeids):
    """Add an empty testcase report to the test report."""
    full_suite_name, case_name, case_params = _split_nodeid(item.nodeid)
    suite_name = _short_suite_name(full_suite_name)

    try:
        suite_report = test_report[suite_name]
    except KeyError:
        suite_report = TestGroupReport(
            name=suite_name,
            uid=suite_name,
            category=ReportCategories.TESTSUITE,
        )
        test_report.append(suite_report)
        nodeids["testsuites"][suite_name] = full_suite_name

    if case_params:
        try:
            param_report = suite_report[case_name]
        except KeyError:
            param_report = TestGroupReport(
                name=case_name,
                uid=case_name,
                category=ReportCategories.PARAMETRIZATION,
            )
            suite_report.append(param_report)
            nodeids["testcases"][suite_name][case_name] = "::".join(
                (full_suite_name, case_name)
            )

        param_case_name = "{}[{}]".format(case_name, case_params)
        param_report.append(
            TestCaseReport(name=param_case_name, uid=param_case_name)
        )
        nodeids["testcases"][suite_name][param_case_name] = item.nodeid
    else:
        suite_report.append(TestCaseReport(name=case_name, uid=case_name))
        nodeids["testcases"][suite_name][case_name] = item.nodeid
