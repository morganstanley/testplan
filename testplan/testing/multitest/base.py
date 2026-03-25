"""MultiTest test execution framework."""

import collections.abc
import concurrent.futures
import functools
import itertools
import warnings
from typing import (
    Any,
    Callable,
    Dict,
    Generator,
    Iterator,
    List,
    Optional,
    OrderedDict,
    Sequence,
    Tuple,
    Union,
)

from schema import And, Or, Use

from testplan.common import config, entity
from testplan.common.utils import interface, strings, timing, watcher
from testplan.common.utils.composer import compose_contexts
from testplan.common.utils.observability import TraceLevel, tracing
from testplan.common.report import (
    ReportCategories,
    RuntimeStatus,
    Status,
)
from testplan.report import (
    TestCaseReport,
    TestGroupReport,
)
from testplan.testing import base as testing_base, result
from testplan.testing import filtering, tagging
from testplan.testing.common import (
    TEST_PART_PATTERN_FORMAT_STRING,
    SkipStrategy,
)
from testplan.testing.multitest import suite as mtest_suite
from testplan.testing.multitest.entries import base as entries_base
from testplan.testing.ordering import TypedSorter
from testplan.testing.result import report_target
from testplan.testing.multitest.suite import (
    get_suite_metadata,
    get_testcase_metadata,
)
from testplan.testing.multitest.test_metadata import TestMetadata
from testplan.testing.base import TestLifecycle


def iterable_suites(obj: Any) -> List[Any]:
    """Create an iterable suites object."""
    suites: List[Any] = (
        [obj] if not isinstance(obj, collections.abc.Iterable) else list(obj)
    )

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
        test_targets[shallow_report["parent_uids"][2]] = (
            _extract_parametrized_testcase_targets(shallow_report)
        )
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
        name: Optional[str] = None
        report: Optional[TestCaseReport] = None

    def __init__(self) -> None:
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

    def __getattr__(self, attr: str) -> Any:
        return getattr(self._environment, attr)

    def __setattr__(self, name: str, value: Any) -> None:
        setattr(self._environment, name, value)

    def __getitem__(self, item: str) -> Any:
        return self._environment[item]

    def __contains__(self, item: object) -> bool:
        return item in self._environment

    def __iter__(self) -> Iterator[Any]:
        return iter(self._environment)

    def __len__(self) -> int:
        return len(self._environment)


def deprecate_stop_on_error(user_input: bool) -> Optional[bool]:
    if user_input == False:
        warnings.warn(
            "``stop_on_error`` in MultiTest constructor has been deprecated, "
            "current default behaviour is equivalent to ``stop_on_error=False``, "
            "thus it's safe to erase it.",
            DeprecationWarning,
        )
        return None
    warnings.warn(
        "``stop_on_error`` in MultiTest constructor has been deprecated, "
        'please use ``skip_strategy="cases-on-error"`` instead to get the '
        "same behaviour as ``stop_on_error=True``.",
        DeprecationWarning,
    )
    return True


class MultiTestConfig(testing_base.TestConfig):
    """
    Configuration object for
    :py:class:`~testplan.testing.multitest.base.MultiTest` runnable
    test execution framework.
    """

    @classmethod
    def get_options(cls) -> Dict[Any, Any]:
        return {
            "suites": Use(iterable_suites),
            config.ConfigOption("thread_pool_size", default=0): int,
            config.ConfigOption("max_thread_pool_size", default=10): int,
            config.ConfigOption("stop_on_error", default=None): And(
                bool, Use(deprecate_stop_on_error)
            ),
            config.ConfigOption("part", default=None): Or(
                None,
                And(
                    (int,),
                    lambda tup: (
                        len(tup) == 2 and 0 <= tup[0] < tup[1] and tup[1] > 1
                    ),
                ),
            ),
            config.ConfigOption("testcase_report_target", default=True): bool,
            config.ConfigOption("testcase_timeout"): Or(
                None, And(int, lambda t: t >= 0)
            ),
        }


class MultiTest(testing_base.Test):
    """
    Starts a local :py:class:`~testplan.common.entity.base.Environment` of
    :py:class:`~testplan.testing.multitest.driver.base.Driver` instances and
    executes :py:func:`testsuites <testplan.testing.multitest.suite.testsuite>`
    against it.

    :param name: Test instance name, often used as uid of test entity.
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
    :type part: ``tuple[int, int]``
    :type result: :py:class:`~testplan.testing.multitest.result.result.Result`
    :param testcase_report_target: Whether to mark testcases as assertions for filepath
        and line number information
    :type testcase_report_target: ``bool``
    :param testcase_timeout: Default timeout value in seconds for testcases that don't
        have an explicit timeout set. If not specified, testcases will have no timeout
        by default.
    :type testcase_timeout: ``int`` or ``NoneType``

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
        name: str,
        suites: Any,
        description: Optional[str] = None,
        initial_context: Any = {},
        environment: Any = [],
        dependencies: Any = None,
        thread_pool_size: int = 0,
        max_thread_pool_size: int = 10,
        part: Optional[Tuple[int, int]] = None,
        before_start: Optional[Callable] = None,
        after_start: Optional[Callable] = None,
        before_stop: Optional[Callable] = None,
        after_stop: Optional[Callable] = None,
        stdout_style: Any = None,
        tags: Any = None,
        result: Any = result.Result,
        testcase_report_target: bool = True,
        testcase_timeout: Optional[int] = None,
        **options: Any,
    ) -> None:
        self._tags_index = None

        if "multi_part_uid" in options:
            # might be replaced by multi_part_name_func
            warnings.warn(
                "MultiTest uid can no longer be customised, please remove ``multi_part_uid`` argument.",
                DeprecationWarning,
            )
            del options["multi_part_uid"]
        if "fix_spec_path" in options:
            warnings.warn(
                "``fix_spec_path`` no longer accepted, please remove it."
            )
            del options["fix_spec_path"]

        options.update(self.filter_locals(locals()))
        super(MultiTest, self).__init__(**options)

        # For all suite instances (and their bound testcase methods,
        # along with parametrization template methods)
        # update tag indices with native tags of this instance.

        if self.cfg.tags:
            for suite in self.suites:
                mtest_suite.propagate_tag_indices(suite, self.cfg.tags)

        # MultiTest may start a thread pool for running testcases concurrently,
        # if they are marked with an execution group.
        self._thread_pool: Optional[concurrent.futures.ThreadPoolExecutor] = (
            None
        )

        self.log_suite_lifecycle = functools.partial(
            self._log_lifecycle, indent=testing_base.SUITE_INDENT
        )
        self.log_suite_status = functools.partial(
            self._log_status, indent=testing_base.SUITE_INDENT
        )
        self.log_multitest_status = functools.partial(
            self._log_status, indent=testing_base.TEST_INST_INDENT
        )

        self.watcher = watcher.Watcher()

    @property
    def suites(self) -> List[Any]:
        """Input list of suites."""
        return self.cfg.suites  # type: ignore[no-any-return]

    def uid(self) -> str:
        """
        Instance name uid.
        A Multitest part instance should not have the same uid as its name.
        """
        if self.cfg.part:
            return TEST_PART_PATTERN_FORMAT_STRING.format(
                self.cfg.name, self.cfg.part[0], self.cfg.part[1]
            )
        else:
            return self.cfg.name  # type: ignore[no-any-return]

    def setup(self) -> None:
        """
        Multitest pre-running routines.

        Here related resources haven't been set up while all necessary wires have been connected.
        """

        # watch line features depends on configuration from the outside world
        try:
            tracing_tests = self.cfg.tracing_tests
        except AttributeError:
            tracing_tests = None
        if tracing_tests is not None:
            self.watcher.set_watching_lines(tracing_tests)

        # handle possibly missing ``skip_strategy``
        if not hasattr(self.cfg, "skip_strategy"):
            self.cfg.set_local("skip_strategy", SkipStrategy.noop())

        # handle deprecated ``stop_on_error``
        if self.cfg.stop_on_error:
            o_skip = SkipStrategy.from_option("cases-on-error")
            self.cfg.set_local(
                "skip_strategy", self.cfg.skip_strategy.union(o_skip)
            )

    def get_test_context(self) -> List[Tuple[Any, List[Any]]]:
        """
        Return filtered & sorted list of suites & testcases
        via `cfg.test_filter` & `cfg.test_sorter`.

        :return: Test suites and testcases belong to them.
        :rtype: ``list`` of ``tuple``
        """
        ctx = []

        if (
            isinstance(self.cfg.test_sorter, TypedSorter)
            and self.cfg.test_lister is None
        ):
            self.logger.user_info(
                "%s: %s", self, self.cfg.test_sorter.user_info()
            )
        sorted_suites = self.cfg.test_sorter.sorted_testsuites(self.cfg.suites)

        if hasattr(self.cfg, "xfail_tests") and self.cfg.xfail_tests:
            xfail_data = self.cfg.xfail_tests
        else:
            xfail_data = {}

        for suite in sorted_suites:
            testcases = suite.get_testcases()

            sorted_testcases = (
                testcases
                if getattr(suite, "strict_order", False)
                or not hasattr(self.cfg, "test_sorter")
                else self.cfg.test_sorter.sorted_testcases(suite, testcases)
            )

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

            if testcases_to_run:
                for testcase in testcases_to_run:
                    testcase_instance = ":".join(
                        [
                            self.name,
                            suite.name,
                            testcase.name,
                        ]
                    )
                    data = xfail_data.get(testcase_instance, None)
                    if data is not None:
                        testcase.__func__.__xfail__ = {
                            "reason": data["reason"],
                            "strict": data["strict"],
                        }

                ctx.append((suite, testcases_to_run))

        if self.cfg.part:
            # round-robin at testcase level
            numer, denom = self.cfg.part
            ofst = 0
            ctx_ = []
            for suite, cases in ctx:
                cases_ = [
                    case
                    for idx, case in enumerate(cases)
                    if (idx + ofst) % denom == numer
                ]
                ofst = (ofst + len(cases)) % denom
                if cases_:
                    ctx_.append((suite, cases_))
            return ctx_

        return ctx

    def _dry_run_testsuites(self) -> None:
        suites_to_run = self.test_context

        for testsuite, testcases in suites_to_run:
            testsuite_report = self._new_testsuite_report(testsuite)

            if getattr(testsuite, "setup", None):
                testsuite_report.append(self._suite_related_report("setup"))

            testsuite_report.extend(
                self._testcase_reports(testsuite, testcases)  # type: ignore[arg-type]
            )

            if getattr(testsuite, "teardown", None):
                testsuite_report.append(self._suite_related_report("teardown"))

            self.result.report.append(testsuite_report)  # type: ignore[attr-defined]

    def run_tests(self) -> TestGroupReport:
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
                    if Status.INCOMPLETE.precede(report.status):
                        report.status_override = Status.INCOMPLETE
                    break

                testsuite_report = self._run_suite(testsuite, testcases)
                report.append(testsuite_report)

                style = self.get_stdout_style(testsuite_report.passed)
                if style.display_testsuite:
                    self.log_suite_status(testsuite_report)

                if self.cfg.skip_strategy.should_skip_rest_suites(
                    testsuite_report.status
                ):
                    # omit ``should_stop`` here
                    self.logger.debug(
                        "Stopping execution of remaining testsuites in %s due to "
                        "``skip_strategy`` set to %s",
                        self,
                        self.cfg.skip_strategy.to_option(),
                    )
                    break

                self.log_suite_lifecycle(testsuite, TestLifecycle.SUITE_END)

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
        shallow_report: Optional[Dict] = None,
        **kwargs: Any,
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

    def get_tags_index(self) -> Dict[str, Any]:
        """
        Tags index for a multitest is its native tags merged with tag indices
        from all of its suites. (Suite tag indices will also contain tag
        indices from their testcases as well).
        """
        if self._tags_index is None:
            self._tags_index = tagging.merge_tag_dicts(
                self.cfg.tags or {}, *[s.__tags_index__ for s in self.suites]
            )
        return self._tags_index  # type: ignore[return-value]

    def skip_step(self, step: Callable) -> bool:
        if step == self.apply_xfail_tests:
            return False
        return super().skip_step(step)

    def add_pre_resource_steps(self) -> None:
        """Runnable steps to be executed before environment starts."""

        super(MultiTest, self).add_pre_resource_steps()
        self._add_step(self.make_runpath_dirs)

    def add_post_resource_steps(self) -> None:
        """Runnable steps to run after environment stopped."""
        self._add_step(self.apply_xfail_tests)
        super(MultiTest, self).add_post_resource_steps()

    def add_main_batch_steps(self) -> None:
        """Runnable steps to be executed while environment is running."""
        self._add_step(self.run_tests)
        self._add_step(self.propagate_tag_indices)

    def should_run(self) -> bool:
        """
        MultiTest filters are applied in `get_test_context`
        so we check if `test_context` is not empty.
        If there's no parts, MultiTest should still be ran even if it is empty, add a filter just for the test
        """
        if self.cfg.part:
            return bool(self.test_context)
        return bool(self.test_context) or self.cfg.test_filter.filter_test(
            self
        )

    def aborting(self) -> None:
        """Suppressing not implemented debug log from parent class."""

    def get_metadata(self) -> TestMetadata:
        suites = []
        for suite, testcases in self.test_context:
            suite_metadata = get_suite_metadata(suite, include_testcases=False)
            suite_metadata.test_cases = [
                get_testcase_metadata(tc) for tc in testcases
            ]
            suites.append(suite_metadata)

        return TestMetadata(
            name=self.uid(),
            description=self.cfg.description,
            test_suites=suites,
        )

    def apply_xfail_tests(self) -> None:
        """
        Apply xfail tests specified via --xfail-tests or @test_plan(xfail_tests=...).
        For MultiTest, we only apply MT:*:* & MT:TS:* here.
        Testcase level xfail already applied during test execution.
        """

        test_report = self.result.report  # type: ignore[attr-defined]
        pattern = f"{test_report.name}:*:*"
        self._xfail(pattern, test_report)

        for suite_report in test_report.entries:
            pattern = f"{test_report.name}:{suite_report.name}:*"
            self._xfail(pattern, suite_report)

    @property
    def _thread_pool_size(self) -> int:
        """
        :return: the size of thread pool to use, based on configured limits
        """
        if self.cfg.thread_pool_size > 0:
            return min(  # type: ignore[no-any-return]
                self.cfg.thread_pool_size, self.cfg.max_thread_pool_size
            )
        else:
            return max(  # type: ignore[no-any-return]
                self.cfg.max_thread_pool_size // 2,
                self.DEFAULT_THREAD_POOL_SIZE,
            )

    def _suite_related_report(self, name: str) -> TestCaseReport:
        """
        Return a report for a testsuite-related action, such as setup or
        teardown.
        """
        return TestCaseReport(
            name=name, uid=name, category=ReportCategories.SYNTHESIZED
        )

    def _testcase_reports(
        self,
        testsuite: Any,
        testcases: List[Any],
        status: Optional[Status] = None,
    ) -> List[Union[TestCaseReport, TestGroupReport]]:
        """
        Generate a list of reports for testcases, including parametrization
        groups.
        """
        testcase_reports: List[Union[TestCaseReport, TestGroupReport]] = []
        parametrization_reports: Dict[str, TestGroupReport] = {}

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

    def _new_test_report(self) -> TestGroupReport:
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
            env_status=entity.ResourceStatus.STOPPED,
        )

    def _new_testsuite_report(self, testsuite: Any) -> TestGroupReport:
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

    def _new_testcase_report(self, testcase: Any) -> TestCaseReport:
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

    def _new_parametrized_group_report(
        self, param_template: str, param_method: Any
    ) -> TestGroupReport:
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

    def _execute_step(self, step: Callable, *args: Any, **kwargs: Any) -> None:
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

    def _run_suite(
        self, testsuite: Any, testcases: List[Any]
    ) -> TestGroupReport:
        """Runs a testsuite object and returns its report."""

        self.log_suite_lifecycle(testsuite, TestLifecycle.SUITE_START)

        _check_testcases(testcases)
        testsuite_report = self._new_testsuite_report(testsuite)

        with (
            tracing.conditional_span(
                name=testsuite.name,
                condition=(self.otel_traces >= TraceLevel.TESTSUITE),
            ) as testsuite_span,
            testsuite_report.timer.record("run"),
        ):
            with self.watcher.save_covered_lines_to(testsuite_report):
                setup_report = self._setup_testsuite(testsuite)
            if setup_report is not None:
                testsuite_report.append(setup_report)
                if setup_report.failed:
                    with self.watcher.save_covered_lines_to(testsuite_report):
                        teardown_report = self._teardown_testsuite(testsuite)
                    if teardown_report is not None:
                        testsuite_report.append(teardown_report)
                    tracing.set_span_as_failed(testsuite_span)
                    return testsuite_report

            serial_cases: List[Any]
            parallel_cases: OrderedDict[str, List[Any]]
            if getattr(testsuite, "strict_order", False):
                serial_cases = testcases
                parallel_cases = collections.OrderedDict()
            else:
                serial_cases, parallel_cases = _split_by_exec_group(testcases)
            testcase_reports = self._run_serial_testcases(
                testsuite, serial_cases
            )
            testsuite_report.extend(testcase_reports)  # type: ignore[arg-type]

            # If there was any error in running the serial testcases, we will
            # not continue to run the parallel testcases if configured to
            # stop on errrors. (skip_strategy.case_comparable == Status.ERROR)
            should_stop = self.cfg.skip_strategy.should_skip_rest_cases(
                testsuite_report.status
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
                    testsuite_report.extend(testcase_reports)  # type: ignore[arg-type]
            if should_stop:
                self.logger.debug(
                    "Skipping all parallel cases in %s due to "
                    "``skip_strategy`` set to %s",
                    self,
                    self.cfg.skip_strategy.to_option(),
                )

            with self.watcher.save_covered_lines_to(testsuite_report):
                teardown_report = self._teardown_testsuite(testsuite)
            if teardown_report is not None:
                testsuite_report.append(teardown_report)

            # if testsuite is marked xfail by user, override its status
            if hasattr(testsuite, "__xfail__"):
                testsuite_report.xfail(testsuite.__xfail__["strict"])

            if testsuite_report.failed:
                tracing.set_span_as_failed(testsuite_span)

        testsuite_report.runtime_status = RuntimeStatus.FINISHED

        if self.aborted:
            testsuite_report.status_override = Status.INCOMPLETE

        return testsuite_report

    def _run_serial_testcases(
        self, testsuite: Any, testcases: List[Any]
    ) -> List[Union[TestCaseReport, TestGroupReport]]:
        """Run testcases serially and return a list of test reports."""
        testcase_reports: List[Union[TestCaseReport, TestGroupReport]] = []
        parametrization_reports: Dict[str, TestGroupReport] = {}
        pre_testcase = getattr(testsuite, "pre_testcase", None)
        post_testcase = getattr(testsuite, "post_testcase", None)

        for testcase in testcases:
            if not self.active:
                testcase_report = self._new_testcase_report(testcase)
                testcase_report.status_override = Status.INCOMPLETE
                # break
            else:
                testcase_report = self._run_testcase(
                    testcase, testsuite, pre_testcase, post_testcase
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

            if self.cfg.skip_strategy.should_skip_rest_cases(
                testcase_report.status
            ):
                # omit ``should_stop`` here
                self.logger.debug(
                    "Skipping execution of remaining testcases in %s due to "
                    "``skip_strategy`` set to %s",
                    mtest_suite.get_testsuite_name(testsuite),
                    self.cfg.skip_strategy.to_option(),
                )
                break

        if parametrization_reports:
            for param_report in parametrization_reports.values():
                if param_report.entries:
                    _add_runtime_info(param_report)

        return testcase_reports

    def _run_parallel_testcases(
        self, testsuite: Any, execution_groups: OrderedDict[str, List[Any]]
    ) -> List[Union[TestCaseReport, TestGroupReport]]:
        """
        Schedule parallel testcases to a threadpool, wait for them to complete
        and return a list of testcase reports.
        """
        testcase_reports: List[Union[TestCaseReport, TestGroupReport]] = []
        all_testcases = itertools.chain.from_iterable(
            execution_groups.values()
        )
        parametrization_reports = self._parametrization_reports(
            testsuite, all_testcases
        )
        pre_testcase = getattr(testsuite, "pre_testcase", None)
        post_testcase = getattr(testsuite, "post_testcase", None)

        for exec_group in execution_groups:
            if not self.active:
                break

            self.logger.debug('Running execution group "%s"', exec_group)
            if self._thread_pool is None:
                raise RuntimeError("self._thread_pool must not be None")
            results = [
                self._thread_pool.submit(
                    self._run_testcase,
                    testcase,
                    testsuite,
                    pre_testcase,
                    post_testcase,
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
                if self.cfg.skip_strategy.should_skip_rest_cases(
                    testcase_report.status
                ):
                    should_stop = True

            if should_stop:
                self.logger.debug(
                    "Stopping execution of parallel cases in %s due to "
                    "``skip_strategy`` set to %s",
                    self,
                    self.cfg.skip_strategy.to_option(),
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

    def _parametrization_reports(
        self, testsuite: Any, testcases: Any
    ) -> OrderedDict[str, TestGroupReport]:
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

    def _get_runtime_environment(  # type: ignore[override]
        self, testcase_name: str, testcase_report: TestCaseReport
    ) -> RuntimeEnvironment:
        runtime_info = MultiTestRuntimeInfo()
        runtime_info.testcase.name = testcase_name
        runtime_info.testcase.report = testcase_report
        return RuntimeEnvironment(self.resources, runtime_info)

    def _get_hook_context(
        self, case_report: TestCaseReport
    ) -> Tuple[Any, ...]:
        return (
            case_report.timer.record("run"),
            case_report.logged_exceptions(),
            # before/after_start/stop trace info goes to multitest level
            self.watcher.save_covered_lines_to(self.report),
        )

    def _setup_testsuite(self, testsuite: Any) -> Optional[TestCaseReport]:
        """
        Run the setup for a testsuite, logging any exceptions.
        Return Testcase report for setup, or None if no setup is required.
        """
        return self._run_suite_related(testsuite, "setup")

    def _teardown_testsuite(self, testsuite: Any) -> Optional[TestCaseReport]:
        """
        Run the teardown for a testsuite, logging any exceptions.
        Return Testcase report for teardown, or None if no setup is required.
        """
        return self._run_suite_related(testsuite, "teardown")

    def _run_suite_related(
        self, testsuite: Any, method_name: str
    ) -> Optional[TestCaseReport]:
        """Runs testsuite related special methods setup/teardown/etc."""
        testsuite_method = getattr(testsuite, method_name, None)
        if testsuite_method is None:
            return None
        elif not callable(testsuite_method):
            raise TypeError("{} expected to be callable.".format(method_name))

        if not self.active:
            return None

        if method_name == "setup":
            self.log_suite_lifecycle(testsuite, TestLifecycle.SETUP_START)
        elif method_name == "teardown":
            self.log_suite_lifecycle(testsuite, TestLifecycle.TEARDOWN_START)

        method_report = self._suite_related_report(method_name)
        case_result = self.cfg.result(
            stdout_style=self.stdout_style,
            _scratch=self._scratch,
            _collect_code_context=self.collect_code_context,
        )

        resources = self._get_runtime_environment(
            testcase_name=method_name, testcase_report=method_report
        )

        method_args: Tuple[Any, ...]
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
        pattern = ":".join(
            [
                self.name,
                testsuite.name,
                method_name,
            ]
        )
        self._xfail(pattern, method_report)
        method_report.runtime_status = RuntimeStatus.FINISHED

        if method_name == "setup":
            self.log_suite_lifecycle(testsuite, TestLifecycle.SETUP_END)
        elif method_name == "teardown":
            self.log_suite_lifecycle(testsuite, TestLifecycle.TEARDOWN_END)

        return method_report

    def _run_case_related(
        self,
        method: Callable,
        testcase: Any,
        resources: RuntimeEnvironment,
        case_result: result.Result,
    ) -> None:
        method_args: Tuple[Any, ...]
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
        testcase: Any,
        testsuite: Any,
        pre_testcase: Optional[Callable],
        post_testcase: Optional[Callable],
        testcase_report: Optional[TestCaseReport] = None,
    ) -> TestCaseReport:
        """Runs a testcase method and returns its report."""

        self.log_testcase_lifecycle(testcase, TestLifecycle.TESTCASE_START)

        testcase_report = testcase_report or self._new_testcase_report(
            testcase
        )
        case_result: result.Result = self.cfg.result(
            stdout_style=self.stdout_style,
            _scratch=self.scratch,
            _collect_code_context=self.collect_code_context,
        )

        # as the runtime info currently has only testcase name we create it here
        # later can be moved out to multitest level, and cloned here as
        # testcases may run parallel

        resources = self._get_runtime_environment(
            testcase_name=testcase.name, testcase_report=testcase_report
        )

        if self.cfg.testcase_report_target and self.collect_code_context:
            testcase = report_target(
                func=testcase,
                ref_func=getattr(
                    testsuite,
                    getattr(testcase, "_parametrization_template", ""),
                    None,
                ),
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
                self.log_testcase_status(testcase_report)  # type: ignore[arg-type]

            self.log_testcase_lifecycle(testcase, TestLifecycle.TESTCASE_END)
            return testcase_report

        testcase_span = None
        with (
            tracing.conditional_span(
                name=testcase.name,
                condition=self.otel_traces >= TraceLevel.TESTCASE,
                test_id=f"{self.uid()}:{testsuite.uid()}:{testcase.__name__}",
            ) as testcase_span,
            testcase_report.timer.record("run"),
        ):
            with compose_contexts(
                testcase_report.logged_exceptions(),
                self.watcher.save_covered_lines_to(testcase_report),
            ):
                if pre_testcase is not None and callable(pre_testcase):
                    self.log_testcase_lifecycle(
                        testcase, TestLifecycle.PRE_TESTCASE_START
                    )
                    self._run_case_related(
                        pre_testcase, testcase, resources, case_result
                    )
                    self.log_testcase_lifecycle(
                        testcase, TestLifecycle.PRE_TESTCASE_END
                    )

                time_restriction = getattr(testcase, "timeout", None)
                # Use default testcase timeout from config if no explicit timeout is set
                if time_restriction is None and getattr(
                    self.cfg, "testcase_timeout", None
                ):
                    time_restriction = self.cfg.testcase_timeout
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

            # always run post_testcase
            with compose_contexts(
                testcase_report.logged_exceptions(),
                self.watcher.save_covered_lines_to(testcase_report),
            ):
                if post_testcase is not None and callable(post_testcase):
                    self.log_testcase_lifecycle(
                        testcase, TestLifecycle.POST_TESTCASE_START
                    )
                    self._run_case_related(
                        post_testcase, testcase, resources, case_result
                    )
                    self.log_testcase_lifecycle(
                        testcase, TestLifecycle.POST_TESTCASE_END
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

            if not case_result.passed:
                tracing.set_span_as_failed(testcase_span)

        testcase_report.pass_if_empty()
        testcase_report.runtime_status = RuntimeStatus.FINISHED

        if self.get_stdout_style(testcase_report.passed).display_testcase:
            self.log_testcase_status(testcase_report)  # type: ignore[arg-type]

        self.log_testcase_lifecycle(testcase, TestLifecycle.TESTCASE_END)

        return testcase_report

    def _run_testsuite_iter(
        self, testsuite: Any, testcases: List[Any]
    ) -> Generator[Tuple[Any, List[str]], None, None]:
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

    def _get_parent_uids(self, testsuite: Any, testcase: Any) -> List[str]:
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

    def _skip_testcases(
        self, testsuite: Any, testcases: List[Any]
    ) -> Generator[Tuple[Dict[str, RuntimeStatus], List[str]], None, None]:
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

            yield (
                {"runtime_status": RuntimeStatus.NOT_RUN},
                parent_uids + [testcase.__name__],
            )

    def _run_testcases_iter(
        self, testsuite: Any, testcases: List[Any]
    ) -> Generator[Tuple[Any, List[str]], None, None]:
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
            yield (
                {"runtime_status": RuntimeStatus.RUNNING},
                parent_uids + [testcase.__name__],
            )

            testcase_report = self._run_testcase(
                testcase, testsuite, pre_testcase, post_testcase
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
        self._cfg.part = part  # type: ignore[attr-defined]
        self._init_test_report()

    def unset_part(self) -> None:
        """Disable part feature, "sanitise" patterns as well"""
        self._cfg.part = None  # type: ignore[attr-defined]

        def _drop_parts(f: Any) -> Any:
            if isinstance(f, filtering.Pattern):
                if isinstance(f.test_pattern, tuple):
                    f.test_pattern = f.test_pattern[0]
            return f

        self._cfg.test_filter.map(_drop_parts)
        self._init_test_report()


def _need_threadpool(testsuites: List[Tuple[Any, List[Any]]]) -> bool:
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


def _check_testcases(testcases: List[Any]) -> None:
    """Check that all testcases are correctly marked as such."""
    for tc in testcases:
        if not getattr(tc, "__testcase__", False):
            raise TypeError(
                "Function {} is not marked as a testcase.".format(tc)
            )


def _split_by_exec_group(
    testcases: List[Any],
) -> Tuple[List[Any], OrderedDict[str, List[Any]]]:
    """
    Split testcases into those with an execution group and those without
    one.
    """
    serial_cases: List[Any] = []
    parallel_cases: OrderedDict[str, List[Any]] = collections.OrderedDict()

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


def _add_runtime_info(param_report: TestGroupReport) -> None:
    """
    Add runtime information to parametrized group report.
    :param param_report: parametrized group report
    :return: the parametrized group report with its runtime information
    """
    group_start_time = None
    group_end_time = None
    for testcase in param_report.entries:
        timer = testcase.timer
        start_time = timer["run"][0].start
        end_time = timer["run"][0].end
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
    param_report.timer["run"] = [
        timing.Interval(group_start_time, group_end_time)
    ]
