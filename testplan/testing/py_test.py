"""PyTest test runner."""
import collections
import inspect
import os
import pytest
import re
import schema
import six

from testplan.testing import base as testing
from testplan.common import config
from testplan.testing.multitest.entries import assertions
from testplan.testing.multitest.result import Result as MultiTestResult
from testplan.testing.multitest.entries.schemas.base import registry as schema_registry
from testplan.testing.multitest.entries.stdout.base import registry as stdout_registry
from testplan.report.testing import TestGroupReport, TestCaseReport, Status
from testplan.common.utils.exceptions import format_trace


class PyTestConfig(testing.TestConfig):
    """
    Configuration object for
    :py:class:`~testplan.testing.py_test.PyTest` test runner.
    """

    @classmethod
    def get_options(cls):
        return {
            config.ConfigOption('target'): schema.Or(str, [str]),
            config.ConfigOption('select', default=''): str,
            config.ConfigOption('extra_args', default=None): schema.Or(
                [str], None),
            config.ConfigOption('quiet', default=True): bool
        }


class PyTest(testing.Test):
    """
    PyTest plugin for Testplan. Allows tests written for PyTest to be run from
    Testplan, with the test results logged and included in the Testplan report.
    """

    CONFIG = PyTestConfig

    def __init__(self, **options):
        super(PyTest, self).__init__(**options)

        # Initialise a seperate plugin object to pass to PyTest. This avoids
        # namespace clashes with the PyTest object, since PyTest will scan for
        # methods that look like hooks in the plugin.
        self._pytest_plugin = _PyTestPlugin(self, self.report, self.cfg.quiet)

    def main_batch_steps(self):
        """Specify the test steps: run the tests, then log the results."""
        self._add_step(self.run_tests)
        self._add_step(self.log_test_results)

    def setup(self):
        """Setup the PyTest plugin for the suite."""
        self._pytest_plugin.setup()

    def run_tests(self):
        """Run pytest and wait for it to terminate."""
        if isinstance(self.cfg.target, six.string_types):
            pytest_args = [self.cfg.target]
        else:
            pytest_args = self.cfg.target[:]

        if self.cfg.select:
            pytest_args.extend(['-k', self.cfg.select])

        if self.cfg.extra_args:
            pytest_args.extend(self.cfg.extra_args)

        # Execute pytest with self as a plugin for hook support
        return_code = pytest.main(pytest_args, plugins=[self._pytest_plugin])

        if return_code != 0:
            self.logger.info('pytest exited with return code %d', return_code)


class _PyTestPlugin(object):
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
        :type case_params: ``str`` or ``None``
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
        self._current_result_obj = MultiTestResult(
            stdout_style=self._parent.stdout_style,
            _scratch=self._parent.scratch
        )

    def pytest_runtest_teardown(self, item):
        """
        Hook called by pytest to tear down a test.

        :param item: the test item to tear down (see pytest documentation)
        """
        self._current_result_obj = None

    def pytest_runtest_logreport(self, report):
        """
        Hook called by pytest to report on the result of a test.

        :param report: the test report for the item just tested (see pytest
                       documentation)
        """
        if report.when == 'setup':
            if report.skipped:
                # Status set to be SKIPPED if testcase is marked skip or xfail
                # lower versioned PyTest does not support this feature
                self._current_case_report.status_override = Status.SKIPPED

        elif report.when == 'call':
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
        if call.when == 'memocollect':
            # Failed to collect tests and log an entry in PyTest report
            self._report.logger.error(format_trace(
                inspect.getinnerframes(call.excinfo.tb), call.excinfo.value))
            self._report.status_override = Status.ERROR

        else:
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
