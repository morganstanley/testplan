"""PyTest test runner."""
import collections
import inspect
import os
import pytest
import re
import schema
import six

from testplan.testing import base as testing
from testplan.common import entity
from testplan.common import config
from testplan.testing.multitest.entries import assertions
from testplan.testing.multitest.entries import schemas
from testplan import report


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
            config.ConfigOption('environment', default=None): schema.Or(
                [entity.Resource], None),
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

        # Add the environment to our list of resources.
        if self.cfg.environment is None:
            self.cfg.environment = []

        for resource in self.cfg.environment:
            resource.parent = self
            resource.cfg.parent = self.cfg
            self.resources.add(resource)

        # Initialise a seperate plugin object to pass to PyTest. This avoids
        # namespace clashes with the PyTest object, since PyTest will scan for
        # methods that look like hooks in the plugin.
        self._pytest_plugin = _PyTestPlugin(self.report, self.cfg.quiet)

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

    _COMPARISON = collections.namedtuple('Comparison', ['op', 'left', 'right'])

    def __init__(self, report, quiet):
        self._report = report
        self._quiet = quiet

        # Collection of suite reports - will be intialised by the setup()
        # method.
        self._suite_reports = None

        # The current working testcase report and comparison object. These
        # need to be stored on this object since they are set and read by
        # different callback hooks.
        self._current_case_report = None
        self._current_comparison = None

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
            raise ValueError('invalid nodeid')

        return match.groups()

    def case_report(self, suite_name, case_name):
        """
        Return the case report for the specified suite and case name, creating
        it first if necessary.

        :param suite_name: the suite name to get the report for
        :type suite_name: ``str``
        :param case_name: the case name to get the report for
        :type case_name: ``str``
        :return: the case report
        :rtype: :py:class:`testplan.testing.base.TestCaseReport`
        """
        # suite_reports is a defaultdict so don't have to create
        case_report = self._suite_reports[suite_name].get(case_name)

        if case_report is None:
            # Report doesn't exist yet; create it
            case_report = testing.TestCaseReport(case_name)
            self._suite_reports[suite_name][case_name] = case_report

        return case_report

    def pytest_runtest_setup(self, item):
        """
        Hook called by pytest to set up a test.

        :param item: the test item to set up (see pytest documentation)
        """
        # Extract suite name and case name
        suite_name, case_name, _ = self.case_parse(item.nodeid)
        report = self.case_report(suite_name, case_name)

        try:
          func_doc = item.function.__doc__
        except AttributeError:
          func_doc = None

        if func_doc is not None:
          report.description = os.linesep.join(
            '    {}'.format(line)
            for line in inspect.getdoc(item.function).split(os.linesep))

        self._current_case_report = report

    # Method signature required for pytest interop
    def pytest_runtest_teardown(self, item):
        """Hook called by pytest to tear down a test."""
        self._current_case_report = None

    def pytest_runtest_logreport(self, report):
        """
        Hook called by pytest to report on the result of a test.

        :param report: the test report for the item just tested (see pytest
                       documentation)
        """
        # Don't care about setup/teardown
        if report.when != 'call':
            return

        _, case_name, case_params = self.case_parse(report.nodeid)

        # If we have comparison information, include it
        if self._current_comparison is not None:
            content = '{value} {op} {expected}'.format(
                value=self._current_comparison.left,
                op=self._current_comparison.op,
                expected=self._current_comparison.right)
            self._current_comparison = None
        else:
            content = '{test} {outcome}'.format(test=report.nodeid,
                                                outcome=report.outcome)

        assertion_obj = assertions.RawAssertion(
            description=case_params or case_name,
            content=content,
            passed=report.passed)

        # Add the assertion entry to the case report
        self._current_case_report.append(
            schemas.base.registry.serialize(assertion_obj))

    # Method signature required for pytest interop
    def pytest_assertrepr_compare(self, op, left, right):
        """
        Hook called by pytest when an assertion contains a comparison.

        :param op: the comparison operator
        :param left: the left side of the comparison
        :param right: the right side of the comparison
        """
        self._current_comparison = self._COMPARISON(op, left, right)

    @pytest.hookimpl(trylast=True)
    def pytest_configure(self, config):
        """
        Hook called by pytest upon startup. Disable output to terminal.

        :param config: pytest config object
        """
        if self._quiet:
          config.pluginmanager.unregister(name='terminalreporter')

    # Method signature required for pytest interop
    def pytest_unconfigure(self, config):
        """
        Hook called by pytest before exiting. Collate suite reports.

        :param config: pytest config object
        """
        # Collate suite reports
        for suite_name, cases in self._suite_reports.items():
          suite_report = report.TestGroupReport(
              name=suite_name,
              category='suite')

          for case in cases.values():
            suite_report.append(case)

          self._report.append(suite_report)
