"""Multitest main test execution framework."""

import collections
import functools
import time

from schema import Use

from testplan.common.config import ConfigOption, validate_func
from testplan.common.entity import Resource, Runnable
from testplan.common.utils.interface import (check_signature,
                                             MethodSignatureMismatch)
from testplan.logger import TESTPLAN_LOGGER, get_test_status_message
from testplan.report import TestGroupReport, TestCaseReport
from testplan.report.testing import Status

from testplan.testing import tagging

from .entries.base import Summary
from .result import Result
from .suite import set_testsuite_testcases

from ..base import Test, TestConfig


MULTITEST_INDENT = 2
SUITE_INDENT = 4
TESTCASE_INDENT = 6
ASSERTION_INDENT = 8


def log_status(report, indent):
    msg = indent * ' ' + get_test_status_message(
        name=report.name, passed=report.passed)
    TESTPLAN_LOGGER.test_info(msg)


log_testcase_status = functools.partial(log_status, indent=TESTCASE_INDENT)
log_suite_status = functools.partial(log_status, indent=SUITE_INDENT)
log_multitest_status = functools.partial(log_status, indent=MULTITEST_INDENT)


class Categories(object):

    PARAMETRIZATION = 'parametrization'
    MULTITEST = 'multitest'
    SUITE = 'suite'


class MultiTestConfig(TestConfig):
    """
    Configuration object for
    :py:class:`~testplan.testing.multitest.base.MultiTest` runnable
    test execution framework.
    """

    def configuration_schema(self):
        """
        Schema for options validation and assignment of default values.
        """

        def iterable_suites(obj):
            """Create an iterable suites object."""
            suites = [obj] if not isinstance(obj,
                                             collections.Iterable) else obj
            for suite in suites:
                set_testsuite_testcases(suite)
            return suites

        overrides = {
            'suites': Use(iterable_suites),
            ConfigOption('environment', default=[]): [Resource],
            ConfigOption('before_start', default=None): validate_func(['env']),
            ConfigOption('after_start', default=None): validate_func(['env']),
            ConfigOption(
                'before_stop', default=None): validate_func(['env', 'result']),
            ConfigOption(
                'after_stop', default=None): validate_func(['env', 'result']),
            ConfigOption(
                'result', default=Result): lambda r: isinstance(r(), Result),
        }
        return self.inherit_schema(overrides, super(MultiTestConfig, self))


class MultiTest(Test):
    """
    Starts a local :py:class:`~testplan.common.entity.base.Environment` of
    :py:class:`~testplan.testing.multitest.driver.base.Driver` instances and
    executes :py:func:`testsuites <testplan.testing.multitest.suite.testsuite>`
    against it.

    :param suites: List of
        :py:func:`@testsuite <testplan.testing.multitest.suite.testsuite>`
        decorated class instances containing
        :py:func:`@testcase <testplan..testing.multitest.suite.testcase>`
        decorated methods representing the tests.
    :type suites: ``list``
    :param environment: List of
      :py:class:`drivers <testplan.tesitng.multitest.driver.base.Driver>` to
      be started and made available on tests execution.
    :type environment: ``list``
    :param before_start: Callable to execute before starting the environment.
    :type before_start: ``callable`` taking an environment argument.
    :param after_start: Callable to execute after starting the environment.
    :type after_start: ``callable`` taking an environment argument.
    :param before_stop: Callable to execute before stopping the environment.
    :type before_stop: ``callable`` taking environment and a result arguments.
    :param after_stop: Callable to execute after stopping the environment.
    :type after_stop: ``callable`` taking environment and a result arguments.
    :param result: Result class definition for result object made available
      from within the testcases.
    :type result: :py:class:`~testplan.testing.multitest.result.Result`

    Also inherits all
    :py:class:`~testplan.testing.base.Test` options.
    """
    CONFIG = MultiTestConfig

    enable_deep_filtering = True

    def __init__(self, **options):
        super(MultiTest, self).__init__(**options)

        for resource in self.cfg.environment:
            resource.parent = self
            resource.cfg.parent = self.cfg
            self.resources.add(resource)

        self.result.report = TestGroupReport(
            name=self.cfg.name,
            category=Categories.MULTITEST,
            description=self.cfg.description,
            tags=tagging.get_native_test_tags(self),
            tags_index=tagging.get_test_tags(self),
        )

        self._suite_unique_name = {}
        self._mark_suite_index()
        self.tags = {}

        self._test_context = None

    @property
    def suites(self):
        """Input list of suites."""
        return self.cfg.suites

    def get_test_context(self):
        """
        Return filtered & sorted list of suites & testcases
        via `cfg.test_filter` & `cfg.test_sorter`.
        """
        ctx = []
        test_filter = self.cfg.test_filter
        test_sorter = self.cfg.test_sorter
        sorted_suites = test_sorter.sorted_testsuites(self.cfg.suites)

        for suite in sorted_suites:
            sorted_testcases = test_sorter.sorted_testcases(
                suite.get_testcases().values())

            testcases_to_run = [case for case in sorted_testcases
                                if test_filter.filter(instance=self,
                                                      testsuite=suite,
                                                      testcase=case)]
            if testcases_to_run:
                ctx.append((suite, testcases_to_run))
        return ctx

    def run_tests(self):
        """Test execution loop."""
        ctx = self.test_context[:]

        while self.active:
            if self.status.tag == Runnable.STATUS.RUNNING:
                try:
                    next_suite, testcases = ctx.pop(0)
                except IndexError:
                    style = self.get_stdout_style(self.report.passed)
                    if style.display_multitest:
                        log_multitest_status(self.report)

                    break
                else:
                    testsuite_report = TestGroupReport(
                        name=next_suite.__class__.__name__,
                        description=next_suite.__class__.__doc__,
                        category=Categories.SUITE,
                        tags=tagging.get_native_suite_tags(next_suite),
                        tags_index=tagging.get_suite_tags(next_suite),
                    )
                    self.report.append(testsuite_report)
                    self._run_suite(next_suite, testcases, testsuite_report)
            time.sleep(self.cfg.active_loop_sleep)

    def _mark_suite_index(self):
        """
        Sets a unique suite name to be used by reporting, formed with the
        name of the class and the index of the suite in this MultiTest instance
        """
        for idx, testsuite in enumerate(self.cfg.suites):
            if hasattr(testsuite, 'suite_name'):
                classname = '{}_{}'.format(testsuite.__class__.__name__,
                                           testsuite.suite_name())
            else:
                classname = testsuite.__class__.__name__
            self._suite_unique_name[testsuite] = '{}_{}'.format(classname, idx)

    def _run_suite(self, testsuite, testcases, testsuite_report):
        """Runs a testsuite object and populates its report object."""
        post_testcase = getattr(testsuite, 'post_testcase', None)
        pre_testcase = getattr(testsuite, 'pre_testcase', None)

        with testsuite_report.logged_exceptions():
            self._run_suite_related(testsuite, 'setup', testsuite_report)

        if not testsuite_report.passed:
            with testsuite_report.logged_exceptions():
                self._run_suite_related(testsuite, 'teardown', testsuite_report)
            return

        param_rep_lookup = {}

        while self.active:
            if self.status.tag == Runnable.STATUS.RUNNING:
                try:
                    testcase = testcases.pop(0)
                except IndexError:
                    with testsuite_report.logged_exceptions():
                        self._run_suite_related(testsuite, 'teardown',
                                                testsuite_report)
                    break
                else:
                    param_template = getattr(
                        testcase, '_parametrization_template', None)

                    if param_template:
                        if param_template not in param_rep_lookup:
                            param_method = getattr(testsuite, param_template)
                            param_report = TestGroupReport(
                                name=param_template,
                                description=param_method.__doc__,
                                category=Categories.PARAMETRIZATION,
                                tags=tagging.get_native_testcase_tags(
                                    param_method),
                                tags_index=tagging.merge_tag_dicts(
                                    param_method.generated_tags,
                                    tagging.get_native_suite_tags(testsuite)
                                )
                            )
                            param_rep_lookup[param_template] = param_report
                            testsuite_report.append(param_report)

                        parent_report = param_rep_lookup[param_template]
                    else:
                        parent_report = testsuite_report

                    testcase_report = self._run_testcase(
                        testcase=testcase,
                        pre_testcase=pre_testcase,
                        post_testcase=post_testcase
                    )

                    parent_report.append(testcase_report)
                    # Break the suite execution if a testcase raised.
                    if testcase_report.status == Status.ERROR:
                        with testsuite_report.logged_exceptions():
                            self._run_suite_related(testsuite, 'teardown',
                                                    testsuite_report)
                        break

            time.sleep(self.cfg.active_loop_sleep)

        if self.get_stdout_style(testsuite_report.passed).display_suite:
            log_suite_status(testsuite_report)

    def _run_testcase(self, testcase, pre_testcase, post_testcase):
        """Runs a testcase method and populates its report object."""

        case_result = self.cfg.result(
            stdout_style=self.stdout_style,
            _scratch=self.scratch,
        )

        testcase_report = TestCaseReport(
            name=testcase.__name__,
            description=testcase.__doc__,
            tags=tagging.get_native_testcase_tags(testcase),
            tags_index=tagging.get_testcase_tags(testcase)
        )

        def _run_case_related(method):
            # Does not work if defined as methods in a testsuite.
            # Needs usage of pre/post_testcase decorators.
            check_signature(method, ['name', 'self', 'env', 'result'])
            method(testcase.__name__, self.resources, case_result)

        with testcase_report.timer.record('run'):
            with testcase_report.logged_exceptions():
                if pre_testcase and callable(pre_testcase):
                    _run_case_related(pre_testcase)

                testcase(self.resources, case_result)

                if post_testcase and callable(post_testcase):
                    _run_case_related(post_testcase)

        # Apply testcase level summarization
        if getattr(testcase, 'summarize', False):
            case_result.entries = [Summary(
                entries=case_result.entries,
                num_passing=testcase.summarize_num_passing,
                num_failing=testcase.summarize_num_failing
            )]

        # native assertion objects -> dict form
        testcase_report.extend(case_result.serialized_entries)
        if self.get_stdout_style(testcase_report.passed).display_testcase:
            log_testcase_status(testcase_report)
        return testcase_report

    def _run_suite_related(self, object, method, report):
        """Runs testsuite related special methods setup/teardown/etc."""
        attr = getattr(object, method, None)
        if attr is None:
            return
        elif not callable(attr):
            raise RuntimeError('{} expected to be callable.'.format(method))

        try:
            check_signature(attr, ['self', 'env', 'result'])
        except MethodSignatureMismatch:
            check_signature(attr, ['self', 'env'])
            attr(self.resources)
        else:
            method_report = TestCaseReport(method)
            report.append(method_report)
            case_result = self.cfg.result(stdout_style=self.stdout_style)
            attr(self.resources, case_result)
            method_report.extend(case_result.serialized_entries)

    def skip_step(self, step):
        """Step should be skipped."""
        if step in (self.resources.start, self.resources.stop):
            return False
        elif self.resources.start_exceptions or self.resources.stop_exceptions:
            TESTPLAN_LOGGER.critical('Skipping step %s', step.__name__)
            return True
        return False

    def post_step_call(self, step):
        """Callable to be executed after each step."""
        exceptions = None
        if step == self.resources.start:
            exceptions = self.resources.start_exceptions
        elif step == self.resources.stop:
            exceptions = self.resources.stop_exceptions
        if exceptions:
            for msg in exceptions.values():
                self.result.report.logger.error(msg)
            self.result.report.status_override = Status.ERROR

    def pre_resource_steps(self):
        """Runnable steps to be executed before environment starts."""
        self._add_step(self.make_runpath_dirs)
        if self.cfg.before_start:
            # TODO add TestGroupReport + TestCaseReport
            self._add_step(self.cfg.before_start, self.resources)

    def main_batch_steps(self):
        """Runnable steps to be executed while environment is running."""
        if self.cfg.after_start:
            # TODO add TestGroupReport + TestCaseReport
            self._add_step(self.cfg.after_start, self.resources)
        self._add_step(self.run_tests)
        if self.cfg.before_stop:
            # TODO add TestGroupReport + TestCaseReport
            self._add_step(self.cfg.before_stop, self.resources, self.report)

    def post_resource_steps(self):
        """Runnable steps to be executed after environment stops."""
        if self.cfg.after_stop:
            # TODO add TestGroupReport + TestCaseReport
            self._add_step(self.cfg.after_stop, self.resources, self.report)

    def should_run(self):
        """
        MultiTest filters are applied in `get_test_context`
        so we just check if `test_context` is not empty."""
        return bool(self.test_context)

    def aborting(self):
        """Suppressing not implemented debug log from parent class."""
