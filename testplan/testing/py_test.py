"""PyTest test runner."""
import collections
import inspect
import os
import re

import pytest
import schema
import six

from testplan.testing import base as testing
from testplan.common.config import ConfigOption
from testplan.testing.multitest.entries import assertions
from testplan.testing.multitest.result import Result as MultiTestResult
from testplan.testing.multitest.entries.schemas.base import (
    registry as schema_registry)
from testplan.testing.multitest.entries.stdout.base import (
    registry as stdout_registry)
from testplan.report.testing import TestGroupReport, TestCaseReport, Status
from testplan.common.utils.exceptions import format_trace
from testplan.common.utils import validation


class PyTestConfig(testing.TestConfig):
    """
    Configuration object for
    :py:class:`~testplan.testing.py_test.PyTest` test runner.
    """

    @classmethod
    def get_options(cls):
        return {
            'target': schema.Or(str, [str]),
            ConfigOption('select', default=''): str,
            ConfigOption('extra_args', default=None): schema.Or([str], None),
            ConfigOption('quiet', default=True): bool,
            ConfigOption('result', default=MultiTestResult):
                validation.is_subclass(MultiTestResult),
        }


class PyTest(testing.Test):
    """
    PyTest plugin for Testplan. Allows tests written for PyTest to be run from
    Testplan, with the test results logged and included in the Testplan report.

    :param name: Test instance name. Also used as uid.
    :type name: ``str``
    :param target: Target of PyTest configuration.
    :type target: ``str`` or ``list`` of ``str``
    :param description: Description of test instance.
    :type description: ``str``
    :param select: Selection of PyTest configuration.
    :type select: ``str``
    :param extra_args: Extra arguments passed to pytest.
    :type extra_args: ``NoneType`` or ``list`` of ``str``
    :param quiet: Quiet mode.
    :type quiet: ``bool``
    :param result: Result that contains assertion entries.
    :type result: :py:class:`~testplan.testing.multitest.result.Result`

    Also inherits all
    :py:class:`~testplan.testing.base.Test` options.
    """

    CONFIG = PyTestConfig

    def __init__(self,
        name,
        target,
        description=None,
        select='',
        extra_args=None,
        quiet=True,
        result=MultiTestResult,
        **options
    ):
        options.update(self.filter_locals(locals()))
        super(PyTest, self).__init__(**options)

        # Initialise a seperate plugin object to pass to PyTest. This avoids
        # namespace clashes with the PyTest object, since PyTest will scan for
        # methods that look like hooks in the plugin.
        self._pytest_plugin = _ReportPlugin(self, self.report, self.cfg.quiet)
        self._collect_plugin = _CollectPlugin(self.cfg.quiet)
        self._pytest_args = self._build_pytest_args()

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
        return_code = pytest.main(self._pytest_args,
                                  plugins=[self._pytest_plugin])
        if return_code != 0:
            self.result.report.status_override = Status.ERROR
            self.logger.error('pytest exited with return code %d', return_code)

    def get_test_context(self):
        """
        Inspect the test suites and cases by running PyTest with the
        --collect-only flag and passing in our collection plugin.

        :return: List containing pairs of suite name and testcase names.
        :rtype: List[Tuple[str, List[str]]]
        """
        return_code = pytest.main(self._pytest_args + ['--collect-only'],
                                  plugins=[self._collect_plugin])

        if return_code != 0:
            self.result.report.status_override = Status.ERROR
            self.logger.error('Failed to collect tests, exit code = %d',
                              return_code)
            return []

        # The plugin will handle converting PyTest tests into suites and
        # testcase names.
        return self._collect_plugin.collected

    def _build_pytest_args(self):
        """
         :return: a list of the args to be passed to PyTest
         :rtype: List[str]
         """
        if isinstance(self.cfg.target, six.string_types):
            pytest_args = [self.cfg.target]
        else:
            pytest_args = self.cfg.target[:]

        if self.cfg.select:
            pytest_args.extend(['-k', self.cfg.select])

        if self.cfg.extra_args:
            pytest_args.extend(self.cfg.extra_args)

        return pytest_args


class _ReportPlugin(object):
    """
    Plugin object passed to PyTest. Contains hooks used to update the Testplan
    report with the status of testcases.
    """

    # Regex for parsing suite and case name and case parameters
    _CASE_REGEX = re.compile(
        r'^(?P<suite_name>.+)::'
        r'(?P<case_name>[^\[]+)(?:\[(?P<case_params>.+)\])?$',
        re.DOTALL)

    def __init__(self, parent, report, quiet):
        self._parent = parent
        self._report = report
        self._quiet = quiet

        # Collection of suite reports - will be intialised by the setup()
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

    def case_parse(self, nodeid):
        """
        Parse a nodeid into suite name, case name, and case parameters.

        :param nodeid: the test nodeid
        :type nodeid: ``str``
        :raises ValueError: if nodeid is invalid
        :return: a tuple consisting of (suite name, case name, case parameters)
        :rtype: ``tuple``
        """
        match = self._CASE_REGEX.match(nodeid.replace('::()::', '::'))

        if match is None:
            raise ValueError('Invalid nodeid')

        return match.groups()

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
                report = TestCaseReport(case_name)
                self._suite_reports[suite_name][case_name] = report
            return report
        else:
            group_report = self._suite_reports[suite_name].get(case_name)
            if group_report is None:
                # create group report for parametrized testcases
                group_report = TestGroupReport(
                    name=case_name, category='parametrization')
                self._suite_reports[suite_name][case_name] = group_report

            case_name = '{}[{}]'.format(case_name, case_params)
            try:
                report = group_report.get_by_uid(case_name)
            except:
                # create report of parametrized testcase
                report = TestCaseReport(case_name)
                group_report.append(report)
            return report

    def pytest_runtest_setup(self, item):
        """
        Hook called by pytest to set up a test.

        :param item: the test item to set up (see pytest documentation)
        """
        # Extract suite name, case name and parameters
        suite_name, case_name, case_params = self.case_parse(item.nodeid)
        report = self.case_report(suite_name, case_name, case_params)

        try:
            func_doc = item.function.__doc__
        except AttributeError:
            func_doc = None

        if func_doc is not None:
            report.description = os.linesep.join(
                '    {}'.format(line) for line in inspect.getdoc(
                    item.function).split(os.linesep))

        self._current_case_report = report
        self._current_result_obj = self._parent.cfg.result(
            stdout_style=self._parent.stdout_style,
            _scratch=self._parent.scratch
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
        if report.when == 'setup':
            if report.skipped and self._current_case_report is not None:
                # Status set to be SKIPPED if testcase is marked skip or xfail
                # lower versioned PyTest does not support this feature
                self._current_case_report.status_override = Status.SKIPPED

        elif report.when == 'call':
            if self._current_case_report is None:
                raise RuntimeError(
                    'Cannot store testcase results to report: no report '
                    'object was created.')

            # Add the assertion entry to the case report
            for entry in self._current_result_obj.entries:
                stdout_renderer = stdout_registry[entry]()
                stdout_header = stdout_renderer.get_header(entry)
                stdout_details = stdout_renderer.get_details(entry) or ''

                # Add 'stdout_header' and 'stdout_details' attributes to
                # serialized entries for standard output later
                serialized_entry = schema_registry.serialize(entry)
                serialized_entry.update(stdout_header=stdout_header,
                                        stdout_details=stdout_details)
                self._current_case_report.append(serialized_entry)

    def pytest_exception_interact(self, node, call, report):
        """
        Hook called when an exception raised and it can be handled. This hook
        is only called if the exception is not an PyTest internal exception.

        :param node: PyTest Function or Module object
        :param call: PyTest CallInfo object
        :param report: PyTest TestReport or CollectReport object
        """
        if call.when in ('memocollect', 'collect'):
            # Failed to collect tests: log to console and mark the report as
            # ERROR.
            self._report.logger.error(format_trace(
                inspect.getinnerframes(call.excinfo.tb), call.excinfo.value))
            self._report.status_override = Status.ERROR

        elif self._current_case_report is not None:
            # Log assertion errors or exceptions in testcase report
            traceback = call.excinfo.traceback[-1]
            message = getattr(call.excinfo.value, 'message', None) or \
                      getattr(call.excinfo.value, 'msg', None) or \
                     getattr(call.excinfo.value, 'args', None) or ''
            if isinstance(message, (tuple, list)):
                message = message[0]

            header = (('Assertion - Fail' if
                call.excinfo.typename == 'AssertionError' else
                'Exception raised') if call.when == 'call' else
                    '{} - Fail'.format(call.when))
            details = 'File: {}{}Line: {}{}{}: {}'.format(
                traceback.path.strpath,
                os.linesep,
                traceback.lineno + 1,
                os.linesep,
                call.excinfo.typename,
                message
            ) if call.excinfo.typename == 'AssertionError' else (
                report.longreprtext if hasattr(report, 'longreprtext') else
                    str(report.longrepr))

            assertion_obj = assertions.RawAssertion(
                description=header,
                content=details,
                passed=False
            )
            serialized_obj = schema_registry.serialize(assertion_obj)
            self._current_case_report.append(serialized_obj)
            self._current_case_report.status_override = Status.FAILED
        else:
            self._report.logger.error(
                'Exception occured outside of a testcase: during %s',
                call.when)
            self._report.logger.error(format_trace(
                inspect.getinnerframes(call.excinfo.tb), call.excinfo.value))

    @pytest.hookimpl(trylast=True)
    def pytest_configure(self, config):
        """
        Hook called by pytest upon startup. Disable output to terminal.

        :param config: pytest config object
        """
        if self._quiet:
            config.pluginmanager.unregister(name='terminalreporter')

    def pytest_unconfigure(self, config):
        """
        Hook called by pytest before exiting. Collate suite reports.

        :param config: pytest config object
        """
        # Collate suite reports
        for suite_name, cases in self._suite_reports.items():
            suite_report = TestGroupReport(
                name=suite_name, category='suite')

            for case in cases.values():
                suite_report.append(case)

            self._report.append(suite_report)


class _CollectPlugin(object):
    """
    PyTest plugin used when collecting tests. Provides access to the collected
    test suites and testcases via the `collected` property.
    """

    def __init__(self, quiet):
        self._quiet = quiet
        self._collected = collections.defaultdict(list)

    @pytest.hookimpl(trylast=True)
    def pytest_configure(self, config):
        """
        Hook called by pytest upon startup. Disable output to terminal.

        :param config: pytest config object
        """
        if self._quiet:
            config.pluginmanager.unregister(name='terminalreporter')

    def pytest_collection_modifyitems(self, items):
        """
        PyTest hook. Despite the name we do not intend to modify any of the
        collected items, but we will store off which tests have been collected
        from each module.
        """
        for test in items:
            self._collected[test.module.__name__].append(test.name)

    @property
    def collected(self):
        """
        Provide access to the test suites and functions collected, after running
        PyTest with an instance of this class as a plugin.

        PyTest allows either plain functions or methods on a class to be used
        as testcases. For simplicity we always use the module name as the
        suite name and ignore the class name for methods.

        :return: list of tuples containing suite and test names - can be
                 directly returned by get_test_context().
        :rtype: List[Tuple[str, List[str]]]
        """
        return list(self._collected.items())
