"""MultiTest test execution framework."""
from __future__ import unicode_literals
from __future__ import print_function
from __future__ import division
from __future__ import absolute_import

from builtins import super
from builtins import str
from future import standard_library

standard_library.install_aliases()
import os
import collections
import functools
from concurrent import futures
import itertools

import schema

from testplan.common import config
from testplan.common import entity
from testplan.common.utils import interface
from testplan.common.utils import validation
from testplan.common.utils import timing
from testplan.common.utils import callable as callable_utils
import testplan.report
from testplan.testing import tagging
from testplan.testing import filtering
from testplan.testing.multitest.entries import base as entries_base
from testplan.testing.multitest import result
from testplan.testing.multitest import suite as mtest_suite
from testplan.testing import base as testing_base


def iterable_suites(obj):
    """Create an iterable suites object."""
    suites = [obj] if not isinstance(obj, collections.Iterable) else obj

    for suite in suites:
        mtest_suite.set_testsuite_testcases(suite)
    return suites


class MultitestIRunner(testing_base.TestIRunner):
    """
    Interactive runner of MultiTest class.
    """

    @testing_base.TestIRunner.set_run_status
    def dry_run(self):
        """
        Generator for dry_run execution.
        """
        yield (
            self._runnable.dry_run,
            tuple(),
            {"status": testplan.report.Status.INCOMPLETE},
        )

    @testing_base.TestIRunner.set_run_status
    def run(self, suite="*", case="*"):
        """
        Generator for run execution.
        """
        pattern = filtering.Pattern("*:{}:{}".format(suite, case))
        for entry in self._runnable.get_test_context(test_filter=pattern):
            for case in entry[1]:
                yield (
                    self._runnable.run_tests,
                    tuple(),
                    {"ctx": [(entry[0], [case])]},
                )


class MultiTestConfig(testing_base.TestConfig):
    """
    Configuration object for
    :py:class:`~testplan.testing.multitest.base.MultiTest` runnable
    test execution framework.
    """

    @classmethod
    def get_options(cls):
        return {
            "suites": schema.Use(iterable_suites),
            config.ConfigOption("thread_pool_size", default=0): int,
            config.ConfigOption("max_thread_pool_size", default=10): int,
            config.ConfigOption("stop_on_error", default=True): bool,
            config.ConfigOption("part", default=None): schema.Or(
                None,
                schema.And(
                    (int,),
                    lambda tp: len(tp) == 2
                    and 0 <= tp[0] < tp[1]
                    and tp[1] > 1,
                ),
            ),
            config.ConfigOption(
                "result", default=result.Result
            ): validation.is_subclass(result.Result),
            config.ConfigOption(
                "interactive_runner", default=MultitestIRunner
            ): object,
            config.ConfigOption("fix_spec_path", default=None): schema.Or(
                None, schema.And(str, os.path.exists)
            ),
        }


class MultiTest(testing_base.Test):
    """
    Starts a local :py:class:`~testplan.common.entity.base.Environment` of
    :py:class:`~testplan.testing.multitest.driver.base.Driver` instances and
    executes :py:func:`testsuites <testplan.testing.multitest.suite.testsuite>`
    against it.

    :param name: Test instance name. Also used as uid.
    :type name: ``str``
    :param suites: List of
        :py:func:`@testsuite <testplan.testing.multitest.suite.testsuite>`
        decorated class instances containing
        :py:func:`@testcase <testplan.testing.multitest.suite.testcase>`
        decorated methods representing the tests.
    :type suites: ``list``
    :param description: Description of test instance.
    :type description: ``str``
    :param thread_pool_size: Size of the thread pool which executes testcases
        with execution_group specified in parallel (default 0 means no pool).
    :type thread_pool_size: ``int``
    :param max_thread_pool_size: Maximum number of threads allowed in the pool.
    :type max_thread_pool_size: ``int``
    :param stop_on_error: When exception raised, stop executing remaining
        testcases in the current test suite. Default: True
    :type stop_on_error: ``bool``
    :param part: Execute only a part of the total testcases. MultiTest needs to
        know which part of the total it is. Only works with Multitest.
    :type part: ``tuple`` of (``int``, ``int``)
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
    :param result: Result class definition for result object made available
        from within the testcases.
    :type result: :py:class:`~testplan.testing.multitest.result.result.Result`
    :param interactive_runner: Interactive runner set for the MultiTest.
    :type interactive_runner: Subclass of
        :py:class:`~testplan.testing.multitest.base.MultitestIRunner`
    :param fix_spec_path: Path of fix specification file.
    :type fix_spec_path: ``NoneType`` or ``str``.

    Also inherits all
    :py:class:`~testplan.testing.base.Test` options.
    """

    CONFIG = MultiTestConfig
    DEFAULT_THREAD_POOL_SIZE = 5

    # MultiTest allows deep filtering
    filter_levels = [
        filtering.FilterLevel.TEST,
        filtering.FilterLevel.TESTSUITE,
        filtering.FilterLevel.TESTCASE,
    ]

    def __init__(
        self,
        name,
        suites,
        description=None,
        thread_pool_size=0,
        max_thread_pool_size=10,
        stop_on_error=True,
        part=None,
        before_start=None,
        after_start=None,
        before_stop=None,
        after_stop=None,
        stdout_style=None,
        tags=None,
        result=result.Result,
        interactive_runner=MultitestIRunner,
        fix_spec_path=None,
        **options
    ):
        self._tags_index = None

        options.update(self.filter_locals(locals()))
        super(MultiTest, self).__init__(**options)

        # For all suite instances (and their bound testcase methods,
        # along with parametrization template methods)
        # update tag indices with native tags of this instance.

        if self.cfg.tags:
            for suite in self.suites:
                mtest_suite.propagate_tag_indices(suite, self.cfg.tags)

        self._pre_post_step_report = None

        # MultiTest may start a thread pool for running testcases concurrently,
        # if they are marked with an execution group.
        self._thread_pool = None

        self.log_testcase_status = functools.partial(
            self._log_status, indent=testing_base.TESTCASE_INDENT
        )
        self.log_suite_status = functools.partial(
            self._log_status, indent=testing_base.SUITE_INDENT
        )
        self.log_multitest_status = functools.partial(
            self._log_status, indent=testing_base.TEST_INST_INDENT
        )

    @property
    def pre_post_step_report(self):
        if self._pre_post_step_report is None:
            self._pre_post_step_report = testplan.report.TestGroupReport(
                name="Pre/Post Step Checks",
                category=testplan.report.ReportCategories.TESTSUITE,
                uid="Pre/Post Step Checks",
            )
        return self._pre_post_step_report

    @property
    def suites(self):
        """Input list of suites."""
        return self.cfg.suites

    def get_test_context(self, test_filter=None):
        """
        Return filtered & sorted list of suites & testcases
        via `cfg.test_filter` & `cfg.test_sorter`.

        :return: Test suites and testcases belong to them.
        :rtype: ``list`` of ``tuple``
        """
        ctx = []
        test_filter = test_filter or self.cfg.test_filter
        test_sorter = self.cfg.test_sorter
        sorted_suites = test_sorter.sorted_testsuites(self.cfg.suites)

        for suite in sorted_suites:
            sorted_testcases = test_sorter.sorted_testcases(
                suite.get_testcases()
            )

            testcases_to_run = [
                case
                for case in sorted_testcases
                if test_filter.filter(test=self, suite=suite, case=case)
            ]

            if self.cfg.part and self.cfg.part[1] > 1:
                testcases_to_run = [
                    testcase
                    for (idx, testcase) in enumerate(testcases_to_run)
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
        suites_to_run = self.test_context
        self.result.report = self._new_test_report()

        for testsuite, testcases in suites_to_run:
            testsuite_report = self._new_testsuite_report(testsuite)
            self.result.report.append(testsuite_report)

            if getattr(testsuite, "setup", None):
                testsuite_report.append(
                    self._suite_related_report("setup", status)
                )

            testsuite_report.extend(
                self._testcase_reports(testsuite, testcases, status)
            )

            if getattr(testsuite, "teardown", None):
                testsuite_report.append(
                    self._suite_related_report("teardown", status)
                )

        return self.result

    def run_tests(self, ctx=None, patch_report=False):
        """Test execution loop."""
        testsuites = ctx or self.test_context

        if patch_report:
            report = self._new_test_report()
        else:
            self._init_test_report()
            report = self.report

        report.runtime_status = testplan.report.RuntimeStatus.RUNNING

        with report.timer.record("run"):
            if _need_threadpool(testsuites):
                self._thread_pool = futures.ThreadPoolExecutor(
                    self._thread_pool_size
                )

            for testsuite, testcases in testsuites:
                if not self.active:
                    report.logger.error("Not all of the suites are done.")
                    st = testplan.report.Status.precedent(
                        [report.status, testplan.report.Status.INCOMPLETE]
                    )
                    if st != report.status:
                        report.status_override = (
                            testplan.report.Status.INCOMPLETE
                        )
                    break

                testsuite_report = self._run_suite(testsuite, testcases)
                report.append(testsuite_report)

                style = self.get_stdout_style(testsuite_report.passed)
                if style.display_testsuite:
                    self.log_suite_status(testsuite_report)

            style = self.get_stdout_style(report.passed)
            if style.display_test:
                self.log_multitest_status(report)

            if self._thread_pool is not None:
                self._thread_pool.shutdown()
                self._thread_pool = None

        report.runtime_status = testplan.report.RuntimeStatus.FINISHED

        if patch_report:
            self.report.merge(report, strict=False)

        return report

    def append_pre_post_step_report(self):
        """
        This will be called as a final step after multitest run is
        complete, to group all step check results under a single report.
        """
        if self._pre_post_step_report is not None:
            self.report.append(self._pre_post_step_report)

    def get_tags_index(self):
        """
        Tags index for a multitest is its native tags merged with tag indices
        from all of its suites. (Suite tag indices will also contain tag
        indices from their testcases as well).
        """
        if self._tags_index is None:
            self._tags_index = tagging.merge_tag_dicts(
                self.cfg.tags or {}, *[s.__tags_index__ for s in self.suites]
            )
        return self._tags_index

    def skip_step(self, step):
        """Check if a step should be skipped."""
        if step in (self.resources.start, self.resources.stop):
            return False
        elif self.resources.start_exceptions or self.resources.stop_exceptions:
            self.logger.critical("Skipping step %s", step.__name__)
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
            self.result.report.status_override = testplan.report.Status.ERROR

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
                    label="before_start", func=self.cfg.before_start
                )
            )

    def main_batch_steps(self):
        """Runnable steps to be executed while environment is running."""
        if self.cfg.after_start:
            self._add_step(
                self._wrap_run_step(
                    label="after_start", func=self.cfg.after_start
                )
            )

        self._add_step(self.run_tests)
        self._add_step(self.propagate_tag_indices)

        if self.cfg.before_stop:
            self._add_step(
                self._wrap_run_step(
                    label="before_stop", func=self.cfg.before_stop
                )
            )

    def post_resource_steps(self):
        """Runnable steps to be executed after environment stops."""
        if self.cfg.after_stop:
            self._add_step(
                self._wrap_run_step(
                    label="after_stop", func=self.cfg.after_stop
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

    @property
    def _thread_pool_size(self):
        """
        :return: the size of thread pool to use, based on configured limits
        """
        if self.cfg.thread_pool_size > 0:
            return min(
                self.cfg.thread_pool_size, self.cfg.max_thread_pool_size
            )
        else:
            return max(
                self.cfg.max_thread_pool_size // 2,
                self.DEFAULT_THREAD_POOL_SIZE,
            )

    def _suite_related_report(self, name, status):
        """
        Return a report for a testsuite-related action, such as setup or
        teardown.
        """
        testcase_report = testplan.report.TestCaseReport(
            name, uid=name, suite_related=True
        )
        if status:
            testcase_report.status_override = status

        return testcase_report

    def _testcase_reports(self, testsuite, testcases, status):
        """
        Generate a list of reports for testcases, including parametrization
        groups.
        """
        parametrization_reports = {}
        testcase_reports = []

        for testcase in testcases:
            testcase_report = self._new_testcase_report(testcase)
            if status:
                testcase_report.status_override = status

            param_template = getattr(
                testcase, "_parametrization_template", None
            )
            if param_template:
                if param_template not in parametrization_reports:
                    param_method = getattr(testsuite, param_template)
                    param_report = self._new_parametrized_group_report(
                        param_template, param_method
                    )
                    parametrization_reports[param_template] = param_report
                    testcase_reports.append(param_report)
                parametrization_reports[param_template].append(testcase_report)
            else:
                testcase_reports.append(testcase_report)

        return testcase_reports

    def _new_test_report(self):
        """
        :return: A new and empty test report object for this MultiTest.
        """
        return testplan.report.TestGroupReport(
            name=self.cfg.name,
            description=self.cfg.description,
            category=testplan.report.ReportCategories.MULTITEST,
            uid=self.uid(),
            tags=self.cfg.tags,
            part=self.cfg.part,
            fix_spec_path=self.cfg.fix_spec_path,
            env_status=entity.ResourceStatus.STOPPED,
        )

    def _new_testsuite_report(self, testsuite):
        """
        :return: A new and empty report for a testsuite.
        """
        return testplan.report.TestGroupReport(
            name=mtest_suite.get_testsuite_name(testsuite),
            description=testsuite.__class__.__doc__,
            category=testplan.report.ReportCategories.TESTSUITE,
            uid=mtest_suite.get_testsuite_name(testsuite),
            tags=testsuite.__tags__,
        )

    def _new_testcase_report(self, testcase):
        """
        :return: A new and empty report for a testcase.
        """
        return testplan.report.TestCaseReport(
            name=testcase.__name__,
            description=testcase.__doc__,
            uid=testcase.__name__,
            tags=testcase.__tags__,
        )

    def _new_parametrized_group_report(self, param_template, param_method):
        """
        :return: A new and empty report for a parametrization group.
        """
        return testplan.report.TestGroupReport(
            name=param_template,
            description=param_method.__doc__,
            category=testplan.report.ReportCategories.PARAMETRIZATION,
            uid=param_template,
            tags=param_method.__tags__,
        )

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

    def _run_suite(self, testsuite, testcases):
        """Runs a testsuite object and returns its report."""
        _check_testcases(testcases)
        testsuite_report = self._new_testsuite_report(testsuite)
        testsuite_report.runtime_status = testplan.report.RuntimeStatus.RUNNING

        with testsuite_report.timer.record("run"):
            setup_report = self._setup_testsuite(testsuite)

            if setup_report is not None:
                testsuite_report.append(setup_report)

                if setup_report.failed:
                    return testsuite_report

            serial_cases, parallel_cases = _split_by_exec_group(testcases)
            testcase_reports = self._run_serial_testcases(
                testsuite, serial_cases
            )
            testsuite_report.extend(testcase_reports)

            # If there was any error in running the serial testcases, we will
            # not continue to run the parallel testcases if configured to
            # stop on errrors.
            should_stop = (
                testsuite_report.status == testplan.report.Status.ERROR
                and self.cfg.stop_on_error
            )

            if parallel_cases and not should_stop:
                testcase_reports = self._run_parallel_testcases(
                    testsuite, parallel_cases
                )
                testsuite_report.extend(testcase_reports)

            teardown_report = self._teardown_testsuite(testsuite)
            if teardown_report is not None:
                testsuite_report.append(teardown_report)

        # if testsuite is marked xfail by user, override its status
        if hasattr(testsuite, "__xfail__"):
            testsuite_report.xfail(testsuite.__xfail__["strict"])

        testsuite_report.runtime_status = testplan.report.RuntimeStatus.FINISHED

        return testsuite_report

    def _run_serial_testcases(self, testsuite, testcases):
        """Run testcases serially and return a list of test reports."""
        parametrization_reports = self._parametrization_reports(
            testsuite, testcases
        )
        testcase_reports = []
        pre_testcase = getattr(testsuite, "pre_testcase", None)
        post_testcase = getattr(testsuite, "post_testcase", None)

        for testcase in testcases:
            if not self.active:
                break

            testcase_report = self._run_testcase(
                testcase, pre_testcase, post_testcase
            )

            param_template = getattr(
                testcase, "_parametrization_template", None
            )
            if param_template:
                parametrization_reports[param_template].append(testcase_report)
            else:
                testcase_reports.append(testcase_report)

            if testcase_report.status == testplan.report.Status.ERROR:
                if self.cfg.stop_on_error:
                    self.logger.debug(
                        "Stopping exeucution of testsuite %s due to error.",
                        mtest_suite.get_testsuite_name(testsuite),
                    )
                    break

        # Add all non-empty parametrization reports into the list of returned
        # testcase reports, to be added to the suite report.
        for param_report in parametrization_reports.values():
            if param_report.entries:
                testcase_reports.append(param_report)

        return testcase_reports

    def _run_parallel_testcases(self, testsuite, execution_groups):
        """
        Schedule parallel testcases to a threadpool, wait for them to complete
        and return a list of testcase reports.
        """
        testcase_reports = []
        all_testcases = itertools.chain.from_iterable(
            execution_groups.values()
        )
        parametrization_reports = self._parametrization_reports(
            testsuite, all_testcases
        )
        pre_testcase = getattr(testsuite, "pre_testcase", None)
        post_testcase = getattr(testsuite, "post_testcase", None)

        for exec_group in execution_groups:
            self.logger.debug("Running execution group %s", exec_group)
            results = [
                self._thread_pool.submit(
                    self._run_testcase, testcase, pre_testcase, post_testcase
                )
                for testcase in execution_groups[exec_group]
            ]

            should_stop = False

            for i, future in enumerate(results):
                testcase_report = future.result()

                testcase = execution_groups[exec_group][i]
                param_template = getattr(
                    testcase, "_parametrization_template", None
                )
                if param_template:
                    parametrization_reports[param_template].append(
                        testcase_report
                    )
                else:
                    testcase_reports.append(testcase_report)

                # If any testcase errors and we are configured to stop on
                # errors, we still wait for the rest of the current execution
                # group to finish before stopping.
                if (
                    testcase_report.status == testplan.report.Status.ERROR
                    and self.cfg.stop_on_error
                ):
                    should_stop = True

            if should_stop:
                self.logger.debug(
                    "Stopping execution of testsuite %s due to error.",
                    self.cfg.name,
                )
                break

        # Add all non-empty parametrization reports into the list of returned
        # testcase reports, to be added to the suite report.
        for param_report in parametrization_reports.values():
            if param_report.entries:
                testcase_reports.append(param_report)

        return testcase_reports

    def _parametrization_reports(self, testsuite, testcases):
        """
        Generate parametrization reports for any parametrized testcases.
        """
        parametrization_reports = collections.OrderedDict()

        for testcase in testcases:
            param_template = getattr(
                testcase, "_parametrization_template", None
            )
            if (
                param_template
                and param_template not in parametrization_reports
            ):
                param_method = getattr(testsuite, param_template)
                param_report = self._new_parametrized_group_report(
                    param_template, param_method
                )
                parametrization_reports[param_template] = param_report

        return parametrization_reports

    def _setup_testsuite(self, testsuite):
        """
        Run the setup for a testsuite, logging any exceptions.

        :return: Testcase report for setup, or None if no setup is required.
        """
        return self._run_suite_related(testsuite, "setup")

    def _teardown_testsuite(self, testsuite):
        """
        Run the teardown for a testsuite.

        :return: Testcase report for teardown, or None if no setup is required.
        """
        return self._run_suite_related(testsuite, "teardown")

    def _run_suite_related(self, testsuite, method):
        """Runs testsuite related special methods setup/teardown/etc."""
        attr = getattr(testsuite, method, None)
        if attr is None:
            return None
        elif not callable(attr):
            raise TypeError("{} expected to be callable.".format(method))

        method_report = testplan.report.TestCaseReport(
            method, uid=method, suite_related=True
        )
        case_result = self.cfg.result(stdout_style=self.stdout_style)

        try:
            interface.check_signature(attr, ["self", "env", "result"])
            method_args = (self.resources, case_result)
        except interface.MethodSignatureMismatch:
            interface.check_signature(attr, ["self", "env"])
            method_args = (self.resources,)

        with method_report.logged_exceptions():
            attr(*method_args)
        method_report.extend(case_result.serialized_entries)

        method_report.pass_if_empty()

        return method_report

    def _run_case_related(self, method, testcase, case_result):
        interface.check_signature(method, ["name", "self", "env", "result"])
        method(testcase.__name__, self.resources, case_result)

    def _run_testcase(self, testcase, pre_testcase, post_testcase):
        """Runs a testcase method and returns its report."""
        testcase_report = self._new_testcase_report(testcase)
        testcase_report.runtime_status = testplan.report.RuntimeStatus.RUNNING
        case_result = self.cfg.result(
            stdout_style=self.stdout_style, _scratch=self.scratch
        )

        with testcase_report.timer.record("run"):
            with testcase_report.logged_exceptions():
                if pre_testcase and callable(pre_testcase):
                    self._run_case_related(pre_testcase, testcase, case_result)

                time_restriction = getattr(testcase, "timeout", None)
                if time_restriction:
                    # pylint: disable=unbalanced-tuple-unpacking
                    executed, execution_result = timing.timeout(
                        time_restriction, "Testcase timeout after {} seconds"
                    )(testcase)(self.resources, case_result)
                    if not executed:
                        testcase_report.logger.error(execution_result)
                        testcase_report.status_override = (
                            testplan.report.Status.ERROR
                        )
                else:
                    testcase(self.resources, case_result)

                if post_testcase and callable(post_testcase):
                    self._run_case_related(
                        post_testcase, testcase, case_result
                    )

        # Apply testcase level summarization
        if getattr(testcase, "summarize", False):
            case_result.entries = [
                entries_base.Summary(
                    entries=case_result.entries,
                    num_passing=testcase.summarize_num_passing,
                    num_failing=testcase.summarize_num_failing,
                    key_combs_limit=testcase.summarize_key_combs_limit,
                )
            ]

        # native assertion objects -> dict form
        testcase_report.extend(case_result.serialized_entries)
        testcase_report.attachments.extend(case_result.attachments)

        # If xfailed testcase, force set status_override and update result
        if hasattr(testcase, "__xfail__"):
            testcase_report.xfail(testcase.__xfail__["strict"])

        testcase_report.pass_if_empty()
        testcase_report.runtime_status = testplan.report.RuntimeStatus.FINISHED

        if self.get_stdout_style(testcase_report.passed).display_testcase:
            self.log_testcase_status(testcase_report)

        return testcase_report

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
                stdout_style=self.stdout_style, _scratch=self.scratch
            )

            testcase_report = testplan.report.TestCaseReport(
                name="{} - {}".format(label, func.__name__),
                description=func.__doc__,
            )

            num_args = len(callable_utils.getargspec(func).args)
            args = (
                (self.resources,)
                if num_args == 1
                else (self.resources, case_result)
            )

            with testcase_report.timer.record("run"):
                with testcase_report.logged_exceptions():
                    func(*args)

            testcase_report.extend(case_result.serialized_entries)

            if self.get_stdout_style(testcase_report.passed).display_testcase:
                self.log_testcase_status(testcase_report)

            self.pre_post_step_report.append(testcase_report)

        return _wrapper

    def _log_status(self, report, indent):
        """Log the test status for a report at the given indent level."""
        self.logger.log_test_status(
            name=report.name, status=report.status, indent=indent
        )


def _need_threadpool(testsuites):
    """
    :return: if we need to start a thread pool to run a set of testsuites
        and testcases.
    """
    return any(
        getattr(testcase, "execution_group", None)
        for pair in testsuites
        for testcase in pair[1]
    )


def _check_testcases(testcases):
    """Check that all testcases are correctly marked as such."""
    for tc in testcases:
        if not getattr(tc, "__testcase__", False):
            raise TypeError(
                "Function {} is not marked as a testcase.".format(tc)
            )


def _split_by_exec_group(testcases):
    """
    Split testcases into those with an execution group and those without
    one.
    """
    serial_cases = []
    parallel_cases = collections.OrderedDict()

    for testcase in testcases:
        exec_group = getattr(testcase, "execution_group", None)
        if exec_group:
            if exec_group in parallel_cases:
                parallel_cases[exec_group].append(testcase)
            else:
                parallel_cases[exec_group] = [testcase]
        else:
            serial_cases.append(testcase)

    return serial_cases, parallel_cases
