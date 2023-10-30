"""MultiTest test execution framework."""

import collections.abc
import concurrent
import functools
import itertools
import os
from typing import Callable, Dict, Generator, List, Optional, Tuple

from schema import And, Or, Use

from testplan.common import config, entity
from testplan.common.utils import callable as callable_utils
from testplan.common.utils import (
    interface,
    strings,
    timing,
    validation,
    watcher,
)
from testplan.common.utils.composer import compose_contexts
from testplan.common.utils.path import change_directory
from testplan.report import (
    ReportCategories,
    RuntimeStatus,
    Status,
    TestCaseReport,
    TestGroupReport,
)
from testplan.testing import base as testing_base
from testplan.testing import filtering, tagging
from testplan.testing.common import TEST_PART_PATTERN_FORMAT_STRING
from testplan.testing.multitest import result
from testplan.testing.multitest import suite as mtest_suite
from testplan.testing.multitest.entries import base as entries_base
from testplan.testing.multitest.result import report_target
from testplan.testing.multitest.suite import get_suite_metadata
from testplan.testing.multitest.test_metadata import TestMetadata


def iterable_suites(obj):
    """Create an iterable suites object."""
    suites = [obj] if not isinstance(obj, collections.abc.Iterable) else obj

    # If multiple objects from one test suite class are added into a Multitest,
    # it's better provide naming function to avoid duplicate test suite names.
    name_counts = collections.Counter(
        # After calling `get_testsuite_name` each test suite object has
        # an attribute `name` of string type (value has been verified)
        mtest_suite.get_testsuite_name(suite)
        for suite in suites
    )
    dupe_names = {k for k, v in name_counts.items() if v > 1}

    if len(dupe_names) > 0:
        raise ValueError(
            'Duplicate test suite name found: "{}".'
            " Consider customizing test suite names with argument `name`"
            " in @testsuite decorator.".format(", ".join(dupe_names))
        )

    for suite in suites:
        mtest_suite.set_testsuite_testcases(suite)

    return suites


def _extract_parametrized_testcase_targets(param_entry: Dict) -> List[str]:
    """
    Given a parametrization entry, extracts the testcases.

    :param param_entry: parametrization entry
    :return: list of testcase names
    """
    cases = []
    for entry in param_entry["entries"]:
        cases.append(entry["name"])
    return cases


def _extract_testsuite_targets(suite_entry: Dict) -> List[str]:
    """
    Given a testsuite entry, extracts the testcases.

    :param suite_entry: testsuite entry
    :return: list of testcase names
    """
    cases = []
    for entry in suite_entry["entries"]:
        if entry["category"] == ReportCategories.TESTCASE:
            cases.append(entry["name"])
        elif entry["category"] == ReportCategories.PARAMETRIZATION:
            cases.extend(_extract_parametrized_testcase_targets(entry))
    return cases


def _extract_test_targets(shallow_report: Dict) -> Dict[str, List[str]]:
    """
    Given a shallow report, extracts the test targets.

    :param shallow_report: holds entry name and category for all children
    :return: mapping of target testsuites to target testcases
    """
    test_targets = {}

    category = shallow_report["category"]

    if category == ReportCategories.MULTITEST:
        for suite in shallow_report["entries"]:
            test_targets[suite["name"]] = _extract_testsuite_targets(suite)
    elif category == ReportCategories.TESTSUITE:
        test_targets[shallow_report["name"]] = _extract_testsuite_targets(
            shallow_report
        )
    elif category == ReportCategories.PARAMETRIZATION:
        test_targets[
            shallow_report["parent_uids"][2]
        ] = _extract_parametrized_testcase_targets(shallow_report)
    elif category == ReportCategories.TESTCASE:
        test_targets[shallow_report["parent_uids"][2]] = [
            shallow_report["name"]
        ]

    return test_targets


class MultiTestRuntimeInfo:
    """
    This class provides information about the state of the actual test run
    that is accessible from the testcase through the environment as:
    ``env.runtime_info``

    Currently only the actual testcase name is accessible as:
    ``env.runtime_info.testcase.name``, more info to come.
    """

    class TestcaseInfo:
        name = None
        report = None

    def __init__(self):
        self.testcase = self.TestcaseInfo()


class RuntimeEnvironment:
    """
    A collection of resources accessible through either items or named
    attributes, representing a test environment instance with runtime
    information about the currently executing testcase.

    This class is a tiny wrapper around the :py:class:`Environment` of
    :py:class:`~testplan.testing.base.Test`, delegates all calls to it
    but with a `runtime_info` which serves the runtime information of
    the current thread of execution.
    """

    def __init__(
        self,
        environment: entity.Environment,
        runtime_info: MultiTestRuntimeInfo,
    ):
        self.__dict__["_environment"] = environment
        self.__dict__["runtime_info"] = runtime_info

    def __getattr__(self, attr):
        return getattr(self._environment, attr)

    def __setattr__(self, name, value):
        setattr(self._environment, name, value)

    def __getitem__(self, item):
        return self._environment[item]

    def __contains__(self, item):
        return item in self._environment

    def __iter__(self):
        return iter(self._environment)


class MultiTestConfig(testing_base.TestConfig):
    """
    Configuration object for
    :py:class:`~testplan.testing.multitest.base.MultiTest` runnable
    test execution framework.
    """

    @classmethod
    def get_options(cls):
        return {
            "suites": Use(iterable_suites),
            config.ConfigOption("thread_pool_size", default=0): int,
            config.ConfigOption("max_thread_pool_size", default=10): int,
            config.ConfigOption("stop_on_error", default=True): bool,
            config.ConfigOption("part", default=None): Or(
                None,
                And(
                    (int,),
                    lambda tup: len(tup) == 2
                    and 0 <= tup[0] < tup[1]
                    and tup[1] > 1,
                ),
            ),
            config.ConfigOption("multi_part_uid", default=None): Or(
                None, lambda x: callable(x)
            ),
            config.ConfigOption(
                "result", default=result.Result
            ): validation.is_subclass(result.Result),
            config.ConfigOption("fix_spec_path", default=None): Or(
                None, And(str, os.path.exists)
            ),
            config.ConfigOption("testcase_report_target", default=True): bool,
        }


class MultiTest(testing_base.Test):
    """
    Starts a local :py:class:`~testplan.common.entity.base.Environment` of
    :py:class:`~testplan.testing.multitest.driver.base.Driver` instances and
    executes :py:func:`testsuites <testplan.testing.multitest.suite.testsuite>`
    against it.

    :param name: Test instance name, often used as uid of test entity.
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
    :param multi_part_uid: Custom function to overwrite the uid of test entity
        if `part` attribute is defined, otherwise use default implementation.
    :type multi_part_uid: ``callable``
    :param result: Result class definition for result object made available
        from within the testcases.
    :type result: :py:class:`~testplan.testing.multitest.result.result.Result`
    :param fix_spec_path: Path of fix specification file.
    :type fix_spec_path: ``NoneType`` or ``str``.
    :param testcase_report_target: Whether to mark testcases as assertions for filepath
        and line number information
    :type testcase_report_target: ``bool``

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
        initial_context={},
        environment=[],
        dependencies=None,
        thread_pool_size=0,
        max_thread_pool_size=10,
        stop_on_error=True,
        part=None,
        multi_part_uid=None,
        before_start=None,
        after_start=None,
        before_stop=None,
        after_stop=None,
        stdout_style=None,
        tags=None,
        result=result.Result,
        fix_spec_path=None,
        testcase_report_target=True,
        **options,
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

        self.watcher = watcher.Watcher()

    @property
    def pre_post_step_report(self):
        if self._pre_post_step_report is None:
            self._pre_post_step_report = TestGroupReport(
                name="Before/After Step Checks",
                category=ReportCategories.TESTSUITE,
            )
            self._pre_post_step_report.status = Status.PASSED
        return self._pre_post_step_report

    @property
    def suites(self):
        """Input list of suites."""
        return self.cfg.suites

    def uid(self):
        """
        Instance name uid.
        A Multitest part instance should not have the same uid as its name.
        """
        if self.cfg.part:
            return (
                self.cfg.multi_part_uid(self.cfg.name, self.cfg.part)
                if self.cfg.multi_part_uid
                else TEST_PART_PATTERN_FORMAT_STRING.format(
                    self.cfg.name, self.cfg.part[0], self.cfg.part[1]
                )
            )
        else:
            return self.cfg.name

    def setup(self):
        """
        Multitest pre-running routines.

        Here related resources haven't been set up while all necessary wires have been connected.
        """

        # watch line features depends on configuration from the outside world
        if self.cfg.parent is not None and self.cfg.tracing_tests is not None:
            self.watcher.set_watching_lines(self.cfg.tracing_tests)

    def get_test_context(self):
        """
        Return filtered & sorted list of suites & testcases
        via `cfg.test_filter` & `cfg.test_sorter`.

        :return: Test suites and testcases belong to them.
        :rtype: ``list`` of ``tuple``
        """
        ctx = []
        sorted_suites = self.cfg.test_sorter.sorted_testsuites(self.cfg.suites)

        for suite in sorted_suites:
            testcases = suite.get_testcases()

            sorted_testcases = (
                testcases
                if getattr(suite, "strict_order", False)
                or not hasattr(self.cfg, "test_sorter")
                else self.cfg.test_sorter.sorted_testcases(suite, testcases)
            )

            if self.cfg.part:
                sorted_testcases = [
                    testcase
                    for (idx, testcase) in enumerate(sorted_testcases)
                    if (idx) % self.cfg.part[1] == self.cfg.part[0]
                ]

            testcases_to_run = [
                case
                for case in sorted_testcases
                if self.cfg.test_filter.filter(
                    test=self, suite=suite, case=case
                )
            ]

            # In batch mode if `strict_order` is specified, then either
            # all of the testcases are filtered out, or left unchanged.
            if getattr(suite, "strict_order", False) and 0 < len(
                testcases_to_run
            ) < len(sorted_testcases):
                testcases_to_run = sorted_testcases

            if self.cfg.testcase_report_target:
                testcases_to_run = [
                    report_target(
                        func=testcase,
                        ref_func=getattr(
                            suite,
                            getattr(testcase, "_parametrization_template", ""),
                            None,
                        ),
                    )
                    for testcase in testcases_to_run
                ]

            if testcases_to_run:
                if hasattr(self.cfg, "xfail_tests") and self.cfg.xfail_tests:
                    for testcase in testcases_to_run:
                        testcase_instance = ":".join(
                            [
                                self.name,
                                suite.name,
                                testcase.name,
                            ]
                        )
                        data = self.cfg.xfail_tests.get(
                            testcase_instance, None
                        )
                        if data is not None:
                            testcase.__xfail__ = {
                                "reason": data["reason"],
                                "strict": data["strict"],
                            }

                ctx.append((suite, testcases_to_run))

        return ctx

    def dry_run(self, status=None):
        """
        A testing process that creates a full structured report without
        any assertion entry. Initial status of each entry can be set.
        """
        self._pre_post_step_report = (
            None  # TODO: this needs to be more generic
        )
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

    def run_tests(self):
        """Run all tests as a batch and return the results."""
        testsuites = self.test_context
        report = self.report

        with report.timer.record("run"):
            if _need_threadpool(testsuites):
                self._thread_pool = concurrent.futures.ThreadPoolExecutor(
                    self._thread_pool_size
                )

            for testsuite, testcases in testsuites:
                if not self.active:
                    report.logger.error("Not all of the suites are done.")
                    st = Status.precedent([report.status, Status.INCOMPLETE])
                    if st != report.status:
                        report.status_override = Status.INCOMPLETE
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

        report.runtime_status = RuntimeStatus.FINISHED

        return report

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
        :return: generator yielding testcase reports and UIDs for merge steps
        """
        if shallow_report is None:
            test_filter = filtering.Pattern(
                pattern="*:{}:{}".format(testsuite_pattern, testcase_pattern),
                match_uid=True,
            )
        else:
            test_targets = _extract_test_targets(shallow_report)

        for testsuite, testcases in self.test_context:
            if not self.active:
                break

            if shallow_report is None:
                testcases = [
                    testcase
                    for testcase in testcases
                    if test_filter.filter(
                        test=self, suite=testsuite, case=testcase
                    )
                ]
            else:
                if testsuite.name not in test_targets:
                    continue
                testcases = [
                    testcase
                    for testcase in testcases
                    if testcase.name in test_targets[testsuite.name]
                ]

            if testcases:
                yield from self._run_testsuite_iter(testsuite, testcases)

    def append_pre_post_step_report(self) -> None:
        """
        Pre-resource step to append pre/post step report if any is configured.
        """
        if any(
            [
                self.cfg.before_start,
                self.cfg.after_start,
                self.cfg.before_stop,
                self.cfg.after_stop,
            ],
        ):
            self.report.append(self.pre_post_step_report)

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
        if step in (
            self.resources.start,
            self.resources.stop,
            self.apply_xfail_tests,
        ):
            return False
        elif self.resources.start_exceptions or self.resources.stop_exceptions:
            self.logger.critical('Skipping step "%s"', step.__name__)
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
        super(MultiTest, self).pre_resource_steps()
        self._add_step(self.make_runpath_dirs)
        if self.cfg.before_start:
            self._add_step(
                self._wrap_run_step(
                    label="before_start", func=self.cfg.before_start
                )
            )
        self._add_step(self.append_pre_post_step_report)

    def pre_main_steps(self):
        """Runnable steps to be executed after environment starts."""
        if self.cfg.after_start:
            self._add_step(
                self._wrap_run_step(
                    label="after_start", func=self.cfg.after_start
                )
            )
        super(MultiTest, self).pre_main_steps()

    def main_batch_steps(self):
        """Runnable steps to be executed while environment is running."""
        self._add_step(self.run_tests)
        self._add_step(self.apply_xfail_tests)
        self._add_step(self.propagate_tag_indices)

    def post_main_steps(self):
        """Runnable steps to run before environment stopped."""
        super(MultiTest, self).post_main_steps()
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
        super(MultiTest, self).post_resource_steps()

    def should_run(self):
        """
        MultiTest filters are applied in `get_test_context`
        so we just check if `test_context` is not empty."""
        return bool(self.test_context)

    def aborting(self):
        """Suppressing not implemented debug log from parent class."""

    def start_test_resources(self):
        """
        Start all test resources but do not run any tests. Used in the
        interactive mode when environments may be started/stopped on demand -
        this method handles running the before/after_start callables if
        required.
        """
        # Need to clean up pre/post steps report in the following scenario:
        #   - resources are started
        #   - stopped
        #   - started again
        # Reason is that dry_run only applies for state reset while appending of
        #   the report group happens only in static run we cannot capture
        self._pre_post_step_report = None
        self.make_runpath_dirs()
        if self.cfg.before_start:
            self._wrap_run_step(
                label="before_start", func=self.cfg.before_start
            )()
        with change_directory(self._discover_path):
            self.resources.start()

        if self.cfg.after_start:
            self._wrap_run_step(
                label="after_start", func=self.cfg.after_start
            )()

    def stop_test_resources(self):
        """
        Stop all test resources. As above, this method is used for the
        interactive mode where a test environment may be stopped on-demand.
        Handles running before/after_stop callables if required.
        """
        if self.cfg.before_stop:
            self._wrap_run_step(
                label="before_stop", func=self.cfg.before_stop
            )()

        self.resources.stop()

        if self.cfg.after_stop:
            self._wrap_run_step(label="after_stop", func=self.cfg.after_stop)()

    def get_metadata(self) -> TestMetadata:
        return TestMetadata(
            name=self.uid(),
            description=self.cfg.description,
            test_suites=[get_suite_metadata(suite) for suite in self.suites],
        )

    def apply_xfail_tests(self):
        """
        Apply xfail tests specified via --xfail-tests or @test_plan(xfail_tests=...).
        For MultiTest, we only apply MT:*:* & MT:TS:* here.
        Testcase level xfail already applied during test execution.
        """

        def _xfail(pattern, report):
            if getattr(self.cfg, "xfail_tests", None):
                found = self.cfg.xfail_tests.get(pattern)
                if found:
                    report.xfail(strict=found["strict"])

        test_report = self.result.report
        pattern = f"{test_report.name}:*:*"
        _xfail(pattern, test_report)

        for suite_report in test_report.entries:
            pattern = f"{test_report.name}:{suite_report.name}:*"
            _xfail(pattern, suite_report)

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
        testcase_report = TestCaseReport(
            name=name, uid=name, suite_related=True
        )
        if status:
            testcase_report.status_override = status

        return testcase_report

    def _testcase_reports(self, testsuite, testcases, status):
        """
        Generate a list of reports for testcases, including parametrization
        groups.
        """
        testcase_reports = []
        parametrization_reports = {}

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
        return TestGroupReport(
            name=self.uid(),
            description=self.cfg.description,
            definition_name=self.cfg.name,
            uid=self.uid(),
            category=ReportCategories.MULTITEST,
            tags=self.cfg.tags,
            part=self.cfg.part,
            fix_spec_path=self.cfg.fix_spec_path,
            env_status=entity.ResourceStatus.STOPPED,
        )

    def _new_testsuite_report(self, testsuite):
        """
        :return: A new and empty report for a testsuite.
        """
        return TestGroupReport(
            name=testsuite.name,
            description=strings.get_docstring(testsuite.__class__),
            definition_name=testsuite.name,
            uid=testsuite.uid(),
            category=ReportCategories.TESTSUITE,
            tags=testsuite.__tags__,
            strict_order=testsuite.strict_order,
        )

    def _new_testcase_report(self, testcase):
        """
        :return: A new and empty report for a testcase.
        """
        return TestCaseReport(
            name=testcase.name,
            description=strings.get_docstring(testcase),
            definition_name=testcase.name,
            uid=testcase.__name__,
            tags=testcase.__tags__,
        )

    def _new_parametrized_group_report(self, param_template, param_method):
        """
        :return: A new and empty report for a parametrization group.
        """
        # Don't include the template method's docstring in the report to
        # avoid duplication with the generated testcases.
        return TestGroupReport(
            name=param_method.name,
            description=strings.get_docstring(param_method),
            definition_name=param_template,
            uid=param_template,
            category=ReportCategories.PARAMETRIZATION,
            tags=param_method.__tags__,
            strict_order=param_method.strict_order,
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

        with testsuite_report.timer.record("run"):
            with self.watcher.save_covered_lines_to(testsuite_report):
                setup_report = self._setup_testsuite(testsuite)
            if setup_report is not None:
                testsuite_report.append(setup_report)
                if setup_report.failed:
                    with self.watcher.save_covered_lines_to(testsuite_report):
                        teardown_report = self._teardown_testsuite(testsuite)
                    if teardown_report is not None:
                        testsuite_report.append(teardown_report)
                    return testsuite_report

            serial_cases, parallel_cases = (
                (testcases, [])
                if getattr(testsuite, "strict_order", False)
                else _split_by_exec_group(testcases)
            )
            testcase_reports = self._run_serial_testcases(
                testsuite, serial_cases
            )
            testsuite_report.extend(testcase_reports)

            # If there was any error in running the serial testcases, we will
            # not continue to run the parallel testcases if configured to
            # stop on errrors.
            should_stop = (
                testsuite_report.status == Status.ERROR
                and self.cfg.stop_on_error
            )

            if parallel_cases and not should_stop:
                with self.watcher.disabled(
                    self.logger,
                    "No coverage data will be collected for parallelly "
                    "executed testcases.",
                ):
                    testcase_reports = self._run_parallel_testcases(
                        testsuite, parallel_cases
                    )
                    testsuite_report.extend(testcase_reports)

            with self.watcher.save_covered_lines_to(testsuite_report):
                teardown_report = self._teardown_testsuite(testsuite)
            if teardown_report is not None:
                testsuite_report.append(teardown_report)

        # if testsuite is marked xfail by user, override its status
        if hasattr(testsuite, "__xfail__"):
            testsuite_report.xfail(testsuite.__xfail__["strict"])

        testsuite_report.runtime_status = RuntimeStatus.FINISHED

        return testsuite_report

    def _run_serial_testcases(self, testsuite, testcases):
        """Run testcases serially and return a list of test reports."""
        testcase_reports = []
        parametrization_reports = {}
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

            if testcase_report.status == Status.ERROR:
                if self.cfg.stop_on_error:
                    self.logger.debug(
                        'Stopping exeucution of testsuite "%s" due to error',
                        testsuite.name,
                    )
                    break

        if parametrization_reports:
            for param_report in parametrization_reports.values():
                if param_report.entries:
                    _add_runtime_info(param_report)

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
            self.logger.debug('Running execution group "%s"', exec_group)
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
                    testcase_report.status == Status.ERROR
                    and self.cfg.stop_on_error
                ):
                    should_stop = True

            if should_stop:
                self.logger.debug(
                    'Stopping execution of testsuite "%s" due to error',
                    self.cfg.name,
                )
                break

        # Add all non-empty parametrization reports into the list of returned
        # testcase reports, to be added to the suite report.
        # Calculate runtime of the parametrized group as well
        for param_report in parametrization_reports.values():
            if param_report.entries:
                _add_runtime_info(param_report)
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

    def _get_runtime_environment(self, testcase_name, testcase_report):
        runtime_info = MultiTestRuntimeInfo()
        runtime_info.testcase.name = testcase_name
        runtime_info.testcase.report = testcase_report
        return RuntimeEnvironment(self.resources, runtime_info)

    def _setup_testsuite(self, testsuite):
        """
        Run the setup for a testsuite, logging any exceptions.
        Return Testcase report for setup, or None if no setup is required.
        """
        return self._run_suite_related(testsuite, "setup")

    def _teardown_testsuite(self, testsuite):
        """
        Run the teardown for a testsuite, logging any exceptions.
        Return Testcase report for teardown, or None if no setup is required.
        """
        return self._run_suite_related(testsuite, "teardown")

    def _run_suite_related(self, testsuite, method_name):
        """Runs testsuite related special methods setup/teardown/etc."""
        testsuite_method = getattr(testsuite, method_name, None)
        if testsuite_method is None:
            return None
        elif not callable(testsuite_method):
            raise TypeError("{} expected to be callable.".format(method_name))

        method_report = TestCaseReport(
            name=method_name, uid=method_name, suite_related=True
        )
        case_result = self.cfg.result(
            stdout_style=self.stdout_style, _scratch=self._scratch
        )

        resources = self._get_runtime_environment(
            testcase_name=method_name, testcase_report=method_report
        )

        try:
            interface.check_signature(testsuite_method, ["env", "result"])
            method_args = (resources, case_result)
        except interface.MethodSignatureMismatch:
            interface.check_signature(testsuite_method, ["env"])
            method_args = (resources,)

        with method_report.timer.record("run"):
            with method_report.logged_exceptions():
                time_restriction = getattr(testsuite_method, "timeout", None)
                if time_restriction:
                    # pylint: disable=unbalanced-tuple-unpacking
                    executed, execution_result = timing.timeout(
                        time_restriction,
                        f"`{method_name}` timeout after {{}} second(s)",
                    )(testsuite_method)(*method_args)
                    if not executed:
                        method_report.logger.error(execution_result)
                        method_report.status_override = Status.ERROR
                else:
                    testsuite_method(*method_args)

        method_report.extend(case_result.serialized_entries)
        method_report.attachments.extend(case_result.attachments)
        method_report.pass_if_empty()
        method_report.runtime_status = RuntimeStatus.FINISHED

        return method_report

    def _run_case_related(
        self,
        method: Callable,
        testcase,
        resources: RuntimeEnvironment,
        case_result: result.Result,
    ):
        try:
            interface.check_signature(method, ["name", "env", "result"])
            method_args = (testcase.name, resources, case_result)
        except interface.MethodSignatureMismatch:
            interface.check_signature(
                method, ["name", "env", "result", "kwargs"]
            )
            method_args = (
                testcase.name,
                resources,
                case_result,
                getattr(testcase, "_parametrization_kwargs", {}),
            )

        time_restriction = getattr(method, "timeout", None)

        if time_restriction:
            # pylint: disable=unbalanced-tuple-unpacking
            executed, execution_result = timing.timeout(
                time_restriction,
                f"`{method.__name__}` timeout after {{}} second(s)",
            )(method)(*method_args)
            if not executed:
                raise Exception(execution_result)
        else:
            method(*method_args)

    def _run_testcase(
        self,
        testcase,
        pre_testcase: Callable,
        post_testcase: Callable,
        testcase_report: Optional[TestCaseReport] = None,
    ):
        """Runs a testcase method and returns its report."""

        testcase_report = testcase_report or self._new_testcase_report(
            testcase
        )
        case_result: result.Result = self.cfg.result(
            stdout_style=self.stdout_style, _scratch=self.scratch
        )

        # as the runtime info currently has only testcase name we create it here
        # later can be moved out to multitest level, and cloned here as
        # testcases may run parallel

        resources = self._get_runtime_environment(
            testcase_name=testcase.name, testcase_report=testcase_report
        )

        # specially handle skipped testcases
        if hasattr(testcase, "__should_skip__"):
            with compose_contexts(
                testcase_report.timer.record("run"),
                testcase_report.logged_exceptions(),
            ):
                testcase(resources, case_result)
            testcase_report.extend(case_result.serialized_entries)
            testcase_report.runtime_status = RuntimeStatus.FINISHED
            if self.get_stdout_style(testcase_report.passed).display_testcase:
                self.log_testcase_status(testcase_report)
            return testcase_report

        with testcase_report.timer.record("run"):
            with compose_contexts(
                testcase_report.logged_exceptions(),
                self.watcher.save_covered_lines_to(testcase_report),
            ):
                if pre_testcase and callable(pre_testcase):
                    self._run_case_related(
                        pre_testcase, testcase, resources, case_result
                    )

                time_restriction = getattr(testcase, "timeout", None)
                if time_restriction:
                    # pylint: disable=unbalanced-tuple-unpacking
                    executed, execution_result = timing.timeout(
                        time_restriction,
                        f"`{testcase.name}` timeout after {{}} second(s)",
                    )(testcase)(resources, case_result)
                    if not executed:
                        testcase_report.logger.error(execution_result)
                        testcase_report.status_override = Status.ERROR
                else:
                    testcase(resources, case_result)

            with compose_contexts(
                testcase_report.logged_exceptions(),
                self.watcher.save_covered_lines_to(testcase_report),
            ):
                if post_testcase and callable(post_testcase):
                    self._run_case_related(
                        post_testcase, testcase, resources, case_result
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
        testcase_report.runtime_status = RuntimeStatus.FINISHED

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

            testcase_report = TestCaseReport(
                name="{} - {}".format(label, func.__name__),
                description=strings.get_docstring(func),
            )

            num_args = len(callable_utils.getargspec(func).args)
            resources = self._get_runtime_environment(
                testcase_name=func.__name__, testcase_report=testcase_report
            )

            args = (resources,) if num_args == 1 else (resources, case_result)

            with compose_contexts(
                testcase_report.timer.record("run"),
                testcase_report.logged_exceptions(),
                self.watcher.save_covered_lines_to(self.report),
            ):
                func(*args)

            testcase_report.extend(case_result.serialized_entries)
            testcase_report.attachments.extend(case_result.attachments)

            if self.get_stdout_style(testcase_report.passed).display_testcase:
                self.log_testcase_status(testcase_report)

            testcase_report.pass_if_empty()
            self.pre_post_step_report.append(testcase_report)

        return _wrapper

    def _log_status(self, report, indent):
        """Log the test status for a report at the given indent level."""
        self.logger.log_test_status(
            name=report.name, status=report.status, indent=indent
        )

    def _run_testsuite_iter(self, testsuite, testcases):
        """Runs a testsuite object and returns its report."""
        _check_testcases(testcases)
        setup_report = self._setup_testsuite(testsuite)

        if setup_report is not None:
            yield setup_report, [self.uid(), testsuite.uid()]

            if setup_report.failed:
                # NOTE: we are going to skip the cases and update the status
                for status, parent_uids in self._skip_testcases(
                    testsuite, testcases
                ):
                    yield status, parent_uids
                teardown_report = self._teardown_testsuite(testsuite)
                if teardown_report is not None:
                    yield teardown_report, [self.uid(), testsuite.uid()]
                return

        for testcase_report, parent_uids in self._run_testcases_iter(
            testsuite, testcases
        ):
            yield testcase_report, parent_uids

        teardown_report = self._teardown_testsuite(testsuite)
        if teardown_report is not None:
            yield teardown_report, [self.uid(), testsuite.uid()]

    def _get_parent_uids(self, testsuite, testcase):
        """
        Utility method to get parent UIDs of a particular testcase.

        :param testsuite: suite to which the case belongs
        :param testcase: the testcase for which the UIDs are derived
        :return: list of parent UIDs
        """

        param_template = getattr(testcase, "_parametrization_template", None)
        if param_template:
            parent_uids = [
                self.uid(),
                testsuite.uid(),
                testcase._parametrization_template,
            ]
        else:
            parent_uids = [self.uid(), testsuite.uid()]
        return parent_uids

    def _skip_testcases(self, testsuite, testcases):
        """
        Utility to forcefully skip testcases and modify their runtime status to not
        run. Used during the failed setup scenario to update the runtime status.

        :param testsuite: testsuite to which the testcases belong
        :param testcases: testcases to skip
        :return: generator yielding the not run status for each parent UIDs list
        """
        for testcase in testcases:
            if not self.active:
                break

            parent_uids = self._get_parent_uids(testsuite, testcase)

            yield {"runtime_status": RuntimeStatus.NOT_RUN}, parent_uids + [
                testcase.__name__
            ]

    def _run_testcases_iter(self, testsuite, testcases):
        """
        Run testcases serially and yield testcase reports.

        Note that we never use a thread pool when running iteratively, so all
        testcases (even those marked with an execution group) are run serially.
        """
        pre_testcase = getattr(testsuite, "pre_testcase", None)
        post_testcase = getattr(testsuite, "post_testcase", None)

        for testcase in testcases:
            if not self.active:
                break

            parent_uids = self._get_parent_uids(testsuite, testcase)

            # set the runtime status of testcase report to RUNNING so that
            # client UI can get the change and show testcase is running
            yield {"runtime_status": RuntimeStatus.RUNNING}, parent_uids + [
                testcase.__name__
            ]

            testcase_report = self._run_testcase(
                testcase, pre_testcase, post_testcase
            )
            yield testcase_report, parent_uids

    def set_part(
        self,
        part: Tuple[int, int],
    ) -> None:
        """
        :param part: Enable the part feature and execute only a part of the
            total testcases for an existing Multitest.
        """
        self._cfg.part = part
        self._init_test_report()

    def unset_part(self) -> None:
        """Disable part feature"""
        self._cfg.part = None
        self._init_test_report()


def _need_threadpool(testsuites):
    """
    :return: if we need to start a thread pool to run a set of testsuites
        and testcases.
    """
    return any(
        not getattr(pair[0], "strict_order", False)
        and any(
            getattr(testcase, "execution_group", None) for testcase in pair[1]
        )
        for pair in testsuites
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


def _add_runtime_info(param_report):
    """
    Add runtime information to parametrized group report.
    :param param_report: parametrized group report
    :return: the parametrized group report with its runtime information
    """
    group_start_time = None
    group_end_time = None
    for testcase in param_report.entries:
        timer = testcase.timer
        start_time = timer["run"].start
        end_time = timer["run"].end
        group_start_time = (
            start_time
            if group_start_time is None
            else min(group_start_time, start_time)
        )
        group_end_time = (
            end_time
            if group_end_time is None
            else max(group_end_time, end_time)
        )
    param_report.timer["run"] = timing.Interval(
        group_start_time, group_end_time
    )
