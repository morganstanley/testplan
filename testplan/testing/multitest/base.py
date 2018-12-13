"""Multitest main test execution framework."""

import os
import inspect
import collections
import functools
import time

try:
    from Queue import Queue, Empty
except ImportError:
    from queue import Queue, Empty

from threading import Thread, Lock
from schema import Use, Or, And

from testplan.common.config import ConfigOption, validate_func
from testplan.common.entity import Resource, Runnable
from testplan.common.utils.interface import (
    check_signature, MethodSignatureMismatch
)
from testplan.common.utils.thread import interruptible_join
from testplan.common.utils.validation import is_subclass
from testplan.logger import TESTPLAN_LOGGER, get_test_status_message
from testplan.report import TestGroupReport, TestCaseReport
from testplan.report.testing import Status

from testplan.testing import tagging, filtering

from .entries.base import Summary
from .result import Result
from .suite import set_testsuite_testcases, propagate_tag_indices

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


def iterable_suites(obj):
    """Create an iterable suites object."""
    suites = [obj] if not isinstance(
        obj, collections.Iterable) else obj

    for suite in suites:
        set_testsuite_testcases(suite)
    return suites


class MultiTestConfig(TestConfig):
    """
    Configuration object for
    :py:class:`~testplan.testing.multitest.base.MultiTest` runnable
    test execution framework.
    """

    @classmethod
    def get_options(cls):
        start_stop_signature = Or(
            None,
            validate_func('env'),
            validate_func('env', 'result'),
        )

        return {
            'suites': Use(iterable_suites),
            ConfigOption('environment', default=[]): [Resource],
            ConfigOption('before_start', default=None): start_stop_signature,
            ConfigOption('after_start', default=None): start_stop_signature,
            ConfigOption('before_stop', default=None): start_stop_signature,
            ConfigOption('after_stop', default=None): start_stop_signature,
            ConfigOption('result', default=Result): is_subclass(Result),
            ConfigOption('thread_pool_size', default=0): int,
            ConfigOption('max_thread_pool_size', default=10): int
        }


class MultiTest(Test):
    """
    Starts a local :py:class:`~testplan.common.entity.base.Environment` of
    :py:class:`~testplan.testing.multitest.driver.base.Driver` instances and
    executes :py:func:`testsuites <testplan.testing.multitest.suite.testsuite>`
    against it.

    :param suites: List of
        :py:func:`@testsuite <testplan.testing.multitest.suite.testsuite>`
        decorated class instances containing
        :py:func:`@testcase <testplan.testing.multitest.suite.testcase>`
        decorated methods representing the tests.
    :type suites: ``list``
    :param environment: List of
        :py:class:`drivers <testplan.tesitng.multitest.driver.base.Driver>` to
        be started and made available on tests execution.
    :type environment: ``list``
    :param result: Result class definition for result object made available
        from within the testcases.
    :type result: :py:class:`~testplan.testing.multitest.result.Result`
    :param before_start: Callable to execute before starting the environment.
    :type before_start: ``callable`` taking an environment argument.
    :param after_start: Callable to execute after starting the environment.
    :type after_start: ``callable`` taking an environment argument.
    :param before_stop: Callable to execute before stopping the environment.
    :type before_stop: ``callable`` taking environment and a result arguments.
    :param after_stop: Callable to execute after stopping the environment.
    :type after_stop: ``callable`` taking environment and a result arguments.
    :param part: Execute only a part of the total testcases. MultiTest needs to
                 know which part of the total it is.
    :type part: ``tuple`` of (``int``, ``int``)
    :param thread_pool_size: Size of the thread pool which executes testcases
        with execution_group specified in parallel (default 0 means no pool).
    :type thread_pool_size: ``int``
    :param max_thread_pool_size: Maximum number of threads allowed in the pool.
    :type max_thread_pool_size: ``int``

    Also inherits all
    :py:class:`~testplan.testing.base.Test` options.
    """
    CONFIG = MultiTestConfig

    # MultiTest allows deep filtering
    filter_levels = [
        filtering.FilterLevel.TEST,
        filtering.FilterLevel.SUITE,
        filtering.FilterLevel.CASE,
    ]

    def __init__(self, **options):
        self._tags_index = None

        super(MultiTest, self).__init__(**options)

        for resource in self.cfg.environment:
            resource.parent = self
            resource.cfg.parent = self.cfg
            self.resources.add(resource)

        # For all suite instances (and their bound testcase methods,
        # along with parametrization template methods)
        # update tag indices with native tags of this instance.

        if self.cfg.tags:
            for suite in self.suites:
                propagate_tag_indices(suite, self.cfg.tags)

        self._pre_post_step_report = None

        # The following members are used for parallel execution of testcases
        # which have been put in the same execution group.
        self._testcase_queue = None
        self._thread_pool = []
        self._thread_pool_size = 0
        self._thread_pool_active = False
        self._thread_pool_available = False

    def _execute_step(self, step, *args, **kwargs):
        """
        Full override of the base class, as we can rely on report object
        for logging exceptions.
        """
        with self.report.logged_exceptions():
            try:
                res = step(*args, **kwargs)
                self.result.step_results[step.__name__] = res
                self.status.update_metadata(**{str(step): res})
            except Exception as exc:
                self.result.step_results[step.__name__] = exc
                self.status.update_metadata(**{str(step): exc})
                raise

    @property
    def pre_post_step_report(self):
        if self._pre_post_step_report is None:
            self._pre_post_step_report = TestGroupReport(
                name='Pre/Post Step Checks',
                category=Categories.SUITE,
                uid='Pre/Post Step Checks',
            )
        return self._pre_post_step_report

    def append_pre_post_step_report(self):
        """
        This will be called as a final step after multitest run is
        complete, to group all step check results under a single report.
        """
        if self._pre_post_step_report is not None:
            self.report.append(self._pre_post_step_report)

    @property
    def suites(self):
        """Input list of suites."""
        return self.cfg.suites

    def get_tags_index(self):
        """
        Tags index for a multitest is its native tags merged with tag indices
        from all of its suites. (Suite tag indices will also contain tag
        indices from their testcases as well).
        """
        if self._tags_index is None:
            self._tags_index = tagging.merge_tag_dicts(
                self.cfg.tags or {}, *[s.__tags_index__ for s in self.suites])
        return self._tags_index

    def get_test_context(self):
        """
        Return filtered & sorted list of suites & testcases
        via `cfg.test_filter` & `cfg.test_sorter`.

        :return: Test suites and testcases belong to them.
        :rtype: ``list`` of ``tuple``
        """
        ctx = []
        test_filter = self.cfg.test_filter
        test_sorter = self.cfg.test_sorter
        sorted_suites = test_sorter.sorted_testsuites(self.cfg.suites)

        for suite in sorted_suites:
            sorted_testcases = test_sorter.sorted_testcases(
                suite.get_testcases())

            testcases_to_run = [
                case for case in sorted_testcases
                if test_filter.filter(
                    test=self, suite=suite, case=case)]

            if self.cfg.part and self.cfg.part[1] > 1:
                testcases_to_run = [
                    testcase for (idx, testcase) in enumerate(testcases_to_run)
                    if idx % self.cfg.part[1] == self.cfg.part[0]
                ]

            if testcases_to_run:
                ctx.append((suite, testcases_to_run))

        return ctx

    def dry_run(self, status=None):
        """
        A testing process that creates a full structured report without
        any assertion entry. Initial status of each entry can be set.
        """
        ctx = [(self.test_context[idx][0], self.test_context[idx][1][:])
               for idx in range(len(self.test_context))]

        self.result.report = TestGroupReport(
            name=self.cfg.name,
            description=self.cfg.description,
            category=self.__class__.__name__.lower(),
            uid=self.uid(),
            tags=self.cfg.tags,
        )

        while len(ctx) > 0:
            testsuite, testcases = ctx.pop(0)
            testsuite_report = TestGroupReport(
                name=testsuite.__class__.__name__,
                description=testsuite.__class__.__doc__,
                category=Categories.SUITE,
                uid=testsuite.__class__.__name__,
                tags=testsuite.__tags__,
            )
            self.result.report.append(testsuite_report)

            if getattr(testsuite, 'setup', None):
                testcase_report = TestCaseReport(
                    'setup', uid='setup', suite_related=True)
                testsuite_report.append(testcase_report)
                if status:
                    testcase_report.status_override = status

            param_rep_lookup = {}
            while len(testcases) > 0:
                testcase = testcases.pop(0)
                testcase_report = TestCaseReport(
                    name=testcase.__name__,
                    description=testcase.__doc__,
                    uid=testcase.__name__,
                    tags=testcase.__tags__,
                )
                if status:
                    testcase_report.status_override = status

                param_template = getattr(
                    testcase, '_parametrization_template', None)
                if param_template:
                    if param_template not in param_rep_lookup:
                        param_method = getattr(testsuite, param_template)
                        param_report = TestGroupReport(
                            name=param_template,
                            description=param_method.__doc__,
                            category=Categories.PARAMETRIZATION,
                            uid=param_template,
                            tags=param_method.__tags__,
                        )
                        param_rep_lookup[param_template] = param_report
                        testsuite_report.append(param_report)
                    param_rep_lookup[param_template].append(testcase_report)
                else:
                    testsuite_report.append(testcase_report)

            if getattr(testsuite, 'teardown', None):
                testcase_report= TestCaseReport(
                    'teardown', uid='teardown', suite_related=True)
                testsuite_report.append(testcase_report)
                if status:
                    testcase_report.status_override = status

        return self.result

    def run_tests(self):
        """Test execution loop."""
        ctx = [(self.test_context[idx][0], self.test_context[idx][1][:])
               for idx in range(len(self.test_context))]

        with self.report.timer.record('run'):
            if any(getattr(testcase, 'execution_group', None)
                    for pair in ctx for testcase in pair[1]):
                with self.report.logged_exceptions():
                    try:
                        self._start_thread_pool()
                    except:
                        self._stop_thread_pool()
                        raise

            while self.active:
                if self.status.tag == Runnable.STATUS.RUNNING:
                    try:
                        next_suite, testcases = ctx.pop(0)
                    except IndexError:
                        style = self.get_stdout_style(self.report.passed)
                        if style.display_test:
                            log_multitest_status(self.report)
                        break
                    else:
                        testsuite_report = TestGroupReport(
                            name=next_suite.__class__.__name__,
                            description=next_suite.__class__.__doc__,
                            category=Categories.SUITE,
                            uid=next_suite.__class__.__name__,
                            tags=next_suite.__tags__,
                        )
                        self.report.append(testsuite_report)
                        with testsuite_report.logged_exceptions():
                            self._run_suite(
                                next_suite, testcases, testsuite_report)

                        if self.get_stdout_style(
                                testsuite_report.passed).display_suite:
                            log_suite_status(testsuite_report)

                time.sleep(self.cfg.active_loop_sleep)

            if self._thread_pool_size > 0:
                self._stop_thread_pool()

    def _run_suite(self, testsuite, testcases, testsuite_report):
        """Runs a testsuite object and populates its report object."""
        pre_testcase = getattr(testsuite, 'pre_testcase', None)
        post_testcase = getattr(testsuite, 'post_testcase', None)

        param_rep_lookup = {}
        current_exec_group = ''
        has_execution_group = False

        def create_testcase_report(testcase):
            """Creates report for testcase and append it to parent report."""
            testcase_report = TestCaseReport(
                name=testcase.__name__,
                description=testcase.__doc__,
                uid=testcase.__name__,
                tags=testcase.__tags__,
            )
            param_template = getattr(
                testcase, '_parametrization_template', None)
            if param_template:
                if param_template not in param_rep_lookup:
                    param_method = getattr(testsuite, param_template)
                    param_report = TestGroupReport(
                        name=param_template,
                        description=param_method.__doc__,
                        category=Categories.PARAMETRIZATION,
                        uid=param_template,
                        tags=param_method.__tags__,
                    )
                    param_rep_lookup[param_template] = param_report
                    testsuite_report.append(param_report)
                param_rep_lookup[param_template].append(testcase_report)
            else:
                testsuite_report.append(testcase_report)
            return testcase_report

        with testsuite_report.timer.record('run'):
            with testsuite_report.logged_exceptions():
                self._run_suite_related(testsuite, 'setup', testsuite_report)

            if not testsuite_report.passed:
                with testsuite_report.logged_exceptions():
                    self._run_suite_related(
                        testsuite, 'teardown', testsuite_report)
                return

            if any(getattr(testcase, 'execution_group', None)
                   for testcase in testcases):
                # Testcases not in execution group will run at the beginning
                testcases.sort(
                    key=lambda f: getattr(f, 'execution_group', None) or '')
                has_execution_group = True
                self._thread_pool_available = True

            while self.active:
                if self.status.tag == Runnable.STATUS.RUNNING:
                    try:
                        testcase = testcases.pop(0)
                    except IndexError:
                        break
                    else:
                        exec_group = getattr(testcase, 'execution_group', '')
                        if exec_group:
                            if exec_group != current_exec_group:
                                self._interruptible_testcase_queue_join()
                                current_exec_group = exec_group
                            if not self._thread_pool_available:  # Error found
                                break
                            task = (testcase, pre_testcase, post_testcase,
                                    create_testcase_report(testcase))
                            self._testcase_queue.put(task)
                        else:
                            testcase_report = create_testcase_report(testcase)
                            self._run_testcase(
                                testcase=testcase,
                                pre_testcase=pre_testcase,
                                post_testcase=post_testcase,
                                testcase_report=testcase_report
                            )
                            if testcase_report.status == Status.ERROR:
                                self._thread_pool_available = False
                                break

                time.sleep(self.cfg.active_loop_sleep)

            # Do nothing if testcase queue and thread pool not created
            self._interruptible_testcase_queue_join()

            with testsuite_report.logged_exceptions():
                self._run_suite_related(
                    testsuite, 'teardown', testsuite_report)

            if has_execution_group:
                self._check_testsuite_report(testsuite_report)

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
            method_report = TestCaseReport(
                method, uid=method, suite_related=True)
            report.append(method_report)
            case_result = self.cfg.result(stdout_style=self.stdout_style)
            with method_report.logged_exceptions():
                attr(self.resources, case_result)
            method_report.extend(case_result.serialized_entries)

    def _run_testcase(
            self, testcase, pre_testcase, post_testcase, testcase_report):
        """Runs a testcase method and populates its report object."""
        case_result = self.cfg.result(
            stdout_style=self.stdout_style,
            _scratch=self.scratch,
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
                num_failing=testcase.summarize_num_failing,
                key_combs_limit=testcase.summarize_key_combs_limit
            )]

        # native assertion objects -> dict form
        testcase_report.extend(case_result.serialized_entries)
        if self.get_stdout_style(testcase_report.passed).display_case:
            log_testcase_status(testcase_report)

    def _run_testcase_in_separate_thread(self):
        """Executes a testcase in a separate thread."""
        while self._thread_pool_active and self.active:
            if not self._thread_pool_available:
                time.sleep(self.cfg.active_loop_sleep)
                continue

            try:
                task = self._testcase_queue.get(
                    timeout=self.cfg.active_loop_sleep)
                testcase, pre_testcase, post_testcase, testcase_report = task
            except Empty:
                continue

            self._run_testcase(
                testcase, pre_testcase, post_testcase, testcase_report)

            try:
                self._testcase_queue.task_done()
            except ValueError:
                # When error occurs, testcase queue will be cleared and
                # cannot accept 'task done' signal.
                pass

            if testcase_report.status == Status.ERROR:
                self.logger.debug(
                    'Error executing testcase {} - stop thread pool'.format(
                        testcase.__name__))
                self._thread_pool_available = False

    def _start_thread_pool(self):
        """Start a thread pool for executing testcases in parallel."""
        if not self._testcase_queue:
            self._testcase_queue = Queue()

        self._thread_pool_size = min(self.cfg.thread_pool_size,
                                     self.cfg.max_thread_pool_size) \
            if self.cfg.thread_pool_size > 0 \
            else max(int(self.cfg.max_thread_pool_size / 2), 2)
        self._thread_pool_active = True

        for _ in range(self._thread_pool_size):
            thread = Thread(target=self._run_testcase_in_separate_thread)
            thread.daemon = True
            thread.start()
            self._thread_pool.append(thread)

        self._thread_pool_available = True

    def _stop_thread_pool(self):
        """Stop the thread pool after finish executing testcases."""
        self._thread_pool_available = False
        self._thread_pool_active = False

        for thread in self._thread_pool:
            interruptible_join(thread)

        self._thread_pool = []
        self._thread_pool_size = 0
        self._interruptible_testcase_queue_join()

    def _interruptible_testcase_queue_join(self):
        """Joining a queue without ignoring signal interrupts."""
        while self._thread_pool_active and self.active:
            if not self._thread_pool_available or \
                    not self._testcase_queue or \
                    self._testcase_queue.unfinished_tasks == 0:
                break
            time.sleep(self.cfg.active_loop_sleep)

        # Clear task queue and give up unfinished testcases
        if self._testcase_queue and not self._testcase_queue.empty():
            with self._testcase_queue.mutex:
                self._testcase_queue.queue.clear()
                self._testcase_queue.unfinished_tasks = 0
                self._testcase_queue.all_tasks_done.notify_all()

    def _check_testsuite_report(self, testsuite_report):
        """Wipe off reports of testcases which have no chance to run."""
        def _remove_testcase_report_if_not_run(
                group_report, remove_empty_sub_group=True):
            # If the content of report changed, return True, otherwise False.
            changed = False
            entries = []

            for report in group_report:
                if isinstance(report, TestGroupReport):
                    changed = _remove_testcase_report_if_not_run(
                        report, remove_empty_sub_group)
                    if len(report.entries) > 0 or not remove_empty_sub_group:
                        entries.append(report)
                    else:
                        changed = True
                elif isinstance(report, TestCaseReport):
                    if report.timer or report.name in ('setup', 'teardown'):
                        entries.append(report)
                    else:
                        changed = True

            group_report.entries = entries
            return changed

        if _remove_testcase_report_if_not_run(testsuite_report):
            testsuite_report.build_index()

    def _wrap_run_step(self, func, label):
        """
        Utility wrapper for special step related functions
        (`before_start`, `after_stop` etc.).

        This method wraps post/pre start/stop related functions so that the
        user can optionally make use of assertions if the function accepts
        both ``env`` and ``result`` arguments.

        These functions are also run within report error logging context,
        meaning that if something goes wrong we will have the stack trace
        in the final report.
        """
        @functools.wraps(func)
        def _wrapper():
            case_result = self.cfg.result(
                stdout_style=self.stdout_style,
                _scratch=self.scratch,
            )

            testcase_report = TestCaseReport(
                name='{} - {}'.format(label, func.__name__),
                description=func.__doc__,
            )

            num_args = len(inspect.getargspec(func).args)
            args = (self.resources,) if num_args == 1 else (
                self.resources, case_result)

            with testcase_report.timer.record('run'):
                with testcase_report.logged_exceptions():
                    func(*args)

            testcase_report.extend(case_result.serialized_entries)

            if self.get_stdout_style(testcase_report.passed).display_case:
                log_testcase_status(testcase_report)

            self.pre_post_step_report.append(testcase_report)
        return _wrapper

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

        if step == self.resources.stop:
            drivers = set(self.resources.start_exceptions.keys())
            drivers.update(self.resources.stop_exceptions.keys())
            for driver in drivers:
                if driver.cfg.report_errors_from_logs:
                    error_log = os.linesep.join(driver.fetch_error_log())
                    if error_log:
                        self.result.report.logger.error(error_log)

    def pre_resource_steps(self):
        """Runnable steps to be executed before environment starts."""
        self._add_step(self.make_runpath_dirs)
        if self.cfg.before_start:
            self._add_step(
                self._wrap_run_step(
                    label='before_start',
                    func=self.cfg.before_start
                )
            )

    def main_batch_steps(self):
        """Runnable steps to be executed while environment is running."""
        if self.cfg.after_start:
            self._add_step(
                self._wrap_run_step(
                    label='after_start',
                    func=self.cfg.after_start
                )

            )

        self._add_step(self.run_tests)
        self._add_step(self.propagate_tag_indices)

        if self.cfg.before_stop:
            self._add_step(
                self._wrap_run_step(
                    label='before_stop',
                    func=self.cfg.before_stop
                )
            )

    def post_resource_steps(self):
        """Runnable steps to be executed after environment stops."""
        if self.cfg.after_stop:
            self._add_step(
                self._wrap_run_step(
                    label='after_stop',
                    func=self.cfg.after_stop
                )
            )

        self._add_step(self.append_pre_post_step_report)

    def should_run(self):
        """
        MultiTest filters are applied in `get_test_context`
        so we just check if `test_context` is not empty."""
        return bool(self.test_context)

    def aborting(self):
        """Suppressing not implemented debug log from parent class."""

