"""Tests runner module."""

import inspect
import ipaddress
import math
import os
import random
import re
import shutil
import sys
import tarfile
import time
import traceback
import uuid
import webbrowser
from collections import OrderedDict
from copy import deepcopy
from dataclasses import dataclass
from traceback import format_stack
from typing import (
    TYPE_CHECKING,
    Any,
    Callable,
    Collection,
    Dict,
    Generator,
    List,
    Literal,
    MutableMapping,
    Optional,
    Pattern,
    Set,
    Tuple,
    Type,
    Union,
    cast,
)

import psutil
import zstandard as zstd
from schema import And, Or, Use
from schema import Optional as schemaOptional

from testplan import defaults
from testplan.common.config import ConfigOption
from testplan.common.entity import (
    Resource,
    Runnable,
    RunnableConfig,
    RunnableResult,
    RunnableStatus,
)
from testplan.common.exporters import BaseExporter, ExportContext, run_exporter
from testplan.common.utils.observability import TraceLevel, tracing
from testplan.report.testing.base import TESTCASE_XFAIL_CONDITION_SCHEMA

if TYPE_CHECKING:
    from testplan.common.remote.remote_service import RemoteService
    from testplan.monitor.resource import (
        ResourceMonitorClient,
        ResourceMonitorServer,
    )

from testplan.common.utils import logger, strings
from testplan.common.utils.exceptions import RunpathInUseError
from testplan.common.utils.package import import_tmp_module
from testplan.common.utils.path import default_runpath, makedirs, makeemptydirs
from testplan.common.utils.selector import Expr as SExpr
from testplan.common.utils.selector import apply_single
from testplan.environment import EnvironmentCreator, Environments
from testplan.exporters import testing as test_exporters
from testplan.exporters.testing.base import Exporter
from testplan.exporters.testing.failed_tests import FailedTestLevel
from testplan.report import (
    ReportCategories,
    Status,
    TestCaseReport,
    TestGroupReport,
    TestReport,
)
from testplan.report.filter import ReportingFilter
from testplan.report.testing.styles import Style
from testplan.runners.base import Executor
from testplan.runners.pools.base import Pool
from testplan.runners.pools.tasks import Task, TaskResult
from testplan.runners.pools.tasks.base import (
    TaskTargetInformation,
    is_task_target,
)
from testplan.testing import common, filtering, listing, ordering, tagging
from testplan.testing.base import Test, TestResult
from testplan.testing.listing import Lister
from testplan.testing.multitest import MultiTest
from testplan.testing.result import Result

if sys.version_info < (3, 11):
    from exceptiongroup import ExceptionGroup

TestTask = Union[Test, Task, Callable]


MULTITEST_EXEC_TIME_ADJUST_FACTOR_LB = 0.25


@dataclass
class TaskInformation:
    target: TestTask
    materialized_test: Test
    uid: str
    task_arguments: dict
    num_of_parts: Union[None, int, Literal["auto"]]


def get_exporters(values: Any) -> List[BaseExporter]:
    """
    Validation function for exporter declarations.

    :param values: Single or a list of exporter declaration(s).
    :return: List of initialized exporter objects.
    """

    def get_exporter(value: Any) -> BaseExporter:
        if isinstance(value, BaseExporter):
            return value
        elif isinstance(value, tuple):
            exporter_cls, params = value
            return exporter_cls(**params)  # type: ignore[no-any-return]
        raise TypeError("Invalid exporter value: {}".format(value))

    if values is None:
        return []
    elif isinstance(values, list):
        return [get_exporter(v) for v in values]
    return [get_exporter(values)]


def result_for_failed_task(original_result: TaskResult) -> TestResult:
    """
    Create a new result entry for invalid result retrieved from a resource.
    """
    result = TestResult()
    if original_result.task is None:
        raise RuntimeError("original_result.task must not be None")
    report = TestGroupReport(
        name=original_result.task.uid(), category=ReportCategories.ERROR
    )
    result.report = report  # type: ignore[assignment]
    attrs = [attr for attr in original_result.task.serializable_attrs]
    result_lines = [
        "{}: {}".format(attr, getattr(original_result.task, attr))
        if getattr(original_result.task, attr, None)
        else ""
        for attr in attrs
    ]
    report.logger.error(
        os.linesep.join([line for line in result_lines if line])
    )
    report.logger.error(original_result.reason)
    report.status_override = Status.ERROR
    return result


def validate_lines(d: dict) -> bool:
    for v in d.values():
        if not (
            isinstance(v, list) and all(map(lambda x: isinstance(x, int), v))
        ) and not (isinstance(v, str) and v.strip() == "*"):
            raise ValueError(
                f'Unexpected value "{v}" of type {type(v)} for lines, '
                'list of integer or string literal "*" expected.'
            )
    return True


def check_local_server(browse: Any) -> bool:
    """
    Early exit if local server (`interactive` extra) is not installed when user
    asks for displaying report using local server feature.
    """
    if browse:
        from testplan.web_ui.web_app import WebServer

        del WebServer

    return True


class TestRunnerConfig(RunnableConfig):
    """
    Configuration object for
    :py:class:`~testplan.runnable.TestRunner` runnable object.
    """

    ignore_extra_keys = True

    @classmethod
    def get_options(cls) -> Dict[Any, Any]:
        return {
            "name": str,
            ConfigOption("description", default=None): Or(str, None),
            ConfigOption("logger_level", default=logger.USER_INFO): int,
            ConfigOption("file_log_level", default=logger.DEBUG): int,
            ConfigOption("runpath", default=default_runpath): Or(
                None, str, lambda x: callable(x)
            ),
            ConfigOption("path_cleanup", default=True): bool,
            ConfigOption("all_tasks_local", default=False): bool,
            ConfigOption(
                "shuffle", default=[]
            ): list,  # list of string choices
            ConfigOption(
                "shuffle_seed", default=float(random.randint(1, 9999))
            ): float,
            ConfigOption("exporters", default=None): Use(get_exporters),
            ConfigOption("stdout_style", default=defaults.STDOUT_STYLE): Style,
            ConfigOption("report_dir", default=defaults.REPORT_DIR): Or(
                str, None
            ),
            ConfigOption("xml_dir", default=None): Or(str, None),
            ConfigOption("pdf_path", default=None): Or(str, None),
            ConfigOption("json_path", default=None): Or(str, None),
            ConfigOption("http_url", default=None): Or(str, None),
            ConfigOption("dump_failed_tests", default=None): Or(str, None),
            ConfigOption(
                "failed_tests_level", default=defaults.FAILED_TESTS_LEVEL
            ): FailedTestLevel,
            ConfigOption("pdf_style", default=defaults.PDF_STYLE): Style,
            ConfigOption("report_tags", default=[]): [
                Use(tagging.validate_tag_value)
            ],
            ConfigOption("report_tags_all", default=[]): [
                Use(tagging.validate_tag_value)
            ],
            ConfigOption("browse", default=False): bool,
            ConfigOption("ui_port", default=None): Or(
                None, And(int, check_local_server)
            ),
            ConfigOption(
                "web_server_startup_timeout",
                default=defaults.WEB_SERVER_TIMEOUT,
            ): int,
            ConfigOption(
                "test_filter", default=filtering.Filter()
            ): filtering.BaseFilter,
            ConfigOption(
                "test_sorter", default=ordering.NoopSorter()
            ): ordering.BaseSorter,
            # Test lister is None by default, otherwise Testplan would
            # list tests, not run them
            ConfigOption("test_lister", default=None): Or(
                None, listing.BaseLister, listing.MetadataBasedLister
            ),
            ConfigOption("test_lister_output", default=None): Or(str, None),
            ConfigOption("verbose", default=False): bool,
            ConfigOption("debug", default=False): bool,
            ConfigOption("timeout", default=defaults.TESTPLAN_TIMEOUT): Or(
                None, And(int, lambda t: t >= 0)
            ),
            ConfigOption(
                "testcase_timeout", default=defaults.TESTCASE_TIMEOUT
            ): Or(None, And(int, lambda t: t >= 0)),
            # active_loop_sleep impacts cpu usage in interactive mode
            ConfigOption("active_loop_sleep", default=0.05): float,
            ConfigOption(
                "interactive_handler",
                default=None,
            ): object,
            ConfigOption("extra_deps", default=[]): [
                Or(str, lambda x: inspect.ismodule(x))
            ],
            ConfigOption("label", default=None): Or(None, str),
            ConfigOption("tracing_tests", default=None): Or(
                And(dict, validate_lines),
                None,
            ),
            ConfigOption("tracing_tests_output", default="-"): str,
            ConfigOption("resource_monitor", default=False): bool,
            ConfigOption("reporting_exclude_filter", default=None): Or(
                And(str, Use(ReportingFilter.parse)), None
            ),
            ConfigOption("xfail_tests", default=None): Or(
                {
                    str: {
                        "reason": str,
                        "strict": bool,
                        schemaOptional(
                            "condition"
                        ): TESTCASE_XFAIL_CONDITION_SCHEMA,
                    },
                },
                None,
            ),
            ConfigOption("runtime_data", default={}): Or(dict, None),
            ConfigOption(
                "auto_part_runtime_limit",
                default=defaults.AUTO_PART_RUNTIME_MAX,
            ): Or(int, float, lambda s: s == "auto"),
            ConfigOption(
                "plan_runtime_target", default=defaults.PLAN_RUNTIME_TARGET
            ): Or(int, float, lambda s: s == "auto"),
            ConfigOption(
                "skip_strategy", default=common.SkipStrategy.noop()
            ): Use(common.SkipStrategy.from_option_or_none),
            ConfigOption("driver_info", default=False): bool,
            ConfigOption("collect_code_context", default=False): bool,
            ConfigOption("archive_runpath", default=None): Or(str, None),
            ConfigOption(
                "otel_traces", default=defaults.TRACE_LEVEL
            ): TraceLevel,
            ConfigOption("otel_traceparent", default=None): Or(str, None),
            ConfigOption("otel_logs", default=None): bool,
        }


class TestRunnerStatus(RunnableStatus):
    """
    Status of a
    :py:class:`TestRunner <testplan.runnable.TestRunner>` runnable object.
    """


class TestRunnerResult(RunnableResult):
    """
    Result object of a
    :py:class:`TestRunner <testplan.runnable.TestRunner>` runnable object.
    """

    report: TestReport

    def __init__(self) -> None:
        super(TestRunnerResult, self).__init__()
        self.test_results: OrderedDict[str, TestResult] = OrderedDict()
        self.exporter_results: List[Any] = []
        self.report = None  # type: ignore[assignment]

    @property
    def success(self) -> bool:
        """Run was successful."""
        return not self.report.failed and all(
            [
                exporter_result.success
                for exporter_result in self.exporter_results
            ]
        )


CACHED_TASK_INFO_ATTRIBUTE = "_cached_task_info"


def _attach_task_info(task_info: TaskInformation) -> TestTask:
    """
    Attach task information (TaskInformation) to the task object
    """
    task = task_info.target
    setattr(task, CACHED_TASK_INFO_ATTRIBUTE, task_info)
    return task


def _detach_task_info(task: TestTask) -> TaskInformation:
    """
    Detach task information (TaskInformation) from the task object
    """
    task_info: TaskInformation = getattr(task, CACHED_TASK_INFO_ATTRIBUTE)
    delattr(task, CACHED_TASK_INFO_ATTRIBUTE)
    return task_info


class TestRunner(Runnable):
    r"""
    Adds tests to test
    :py:class:`executor <testplan.runners.base.Executor>` resources
    and invoke report
    :py:class:`exporter <testplan.exporters.testing.base.Exporter>` objects
    to create the
    :py:class:`~testplan.runnable.TestRunnerResult`.

    :param name: Name of test runner.
    :type name: ``str``
    :param description: Description of test runner.
    :type description: ``str``
    :param logger_level: Logger level for stdout.
    :type logger_level: ``int``
    :param: file_log_level: Logger level for file.
    :type file_log_level: ``int``
    :param runpath: Input runpath.
    :type runpath: ``str`` or ``callable``
    :param path_cleanup: Clean previous runpath entries.
    :type path_cleanup: ``bool``
    :param archive_runpath: Directory path to archive the runpath after test execution.
    :type archive_runpath: ``str`` or ``NoneType``
    :param all_tasks_local: Schedule all tasks in local pool
    :type all_tasks_local: ``bool``
    :param shuffle: Shuffle strategy.
    :type shuffle: ``list`` of ``str``
    :param shuffle_seed: Shuffle seed.
    :type shuffle_seed: ``float``
    :param exporters: Exporters for reports creation.
    :type exporters: ``list``
    :param stdout_style: Styling output options.
    :type stdout_style:
        :py:class:`Style <testplan.report.testing.styles.Style>`
    :param report_dir: Report directory.
    :type report_dir: ``str``
    :param xml_dir: XML output directory.
    :type xml_dir: ``str``
    :param pdf_path: PDF output path <PATH>/\*.pdf.
    :type pdf_path: ``str``
    :param json_path: JSON output path <PATH>/\*.json.
    :type json_path: ``str``
    :param pdf_style: PDF creation styling options.
    :type pdf_style: :py:class:`Style <testplan.report.testing.styles.Style>`
    :param http_url: Web url for posting test report.
    :type http_url: ``str``
    :param report_tags: Matches tests marked with any of the given tags.
    :type report_tags: ``list``
    :param report_tags_all: Match tests marked with all of the given tags.
    :type report_tags_all: ``list``
    :param browse: Open web browser to display the test report.
    :type browse: ``bool`` or ``NoneType``
    :param ui_port: Port of web server for displaying test report.
    :type ui_port: ``int`` or ``NoneType``
    :param web_server_startup_timeout: Timeout for starting web server.
    :type web_server_startup_timeout: ``int``
    :param test_filter: Tests filtering class.
    :type test_filter: Subclass of
        :py:class:`BaseFilter <testplan.testing.filtering.BaseFilter>`
    :param test_sorter: Tests sorting class.
    :type test_sorter: Subclass of
        :py:class:`BaseSorter <testplan.testing.ordering.BaseSorter>`
    :param test_lister: Tests listing class.
    :type test_lister: Subclass of
        :py:class:`BaseLister <testplan.testing.listing.BaseLister>`
    :param verbose: Enable or disable verbose mode.
    :type verbose: ``bool``
    :param debug: Enable or disable debug mode.
    :type debug: ``bool``
    :param timeout: Timeout value for test execution.
    :type timeout: ``NoneType`` or ``int`` (greater than 0).
    :param abort_wait_timeout: Timeout for test runner abort.
    :type abort_wait_timeout: ``int``
    :param interactive_handler: Handler for interactive mode execution.
    :type interactive_handler: Subclass of :py:class:
        `TestRunnerIHandler <testplan.runnable.interactive.base.TestRunnerIHandler>`
    :param extra_deps: Extra module dependencies for interactive reload, or
        paths of these modules.
    :type extra_deps: ``list`` of ``module`` or ``str``
    :param label: Label the test report with the given name, useful to
        categorize or classify similar reports .
    :type label: ``str`` or ``NoneType``
    :param runtime_data: Historical runtime data which will be used for
        Multitest auto-part and weight-based Task smart-scheduling
    :type runtime_data: ``dict``
    :param auto_part_runtime_limit: The runtime limitation for auto-part task
    :type auto_part_runtime_limit: ``int`` or ``float`` or literal "auto"
    :param plan_runtime_target: The testplan total runtime limitation for smart schedule
    :type plan_runtime_target: ``int`` or ``float`` or literal "auto"

    Also inherits all
    :py:class:`~testplan.common.entity.base.Runnable` options.
    """

    CONFIG = TestRunnerConfig
    STATUS = TestRunnerStatus
    RESULT = TestRunnerResult

    result: TestRunnerResult

    def __init__(self, **options: Any) -> None:
        # TODO: check options sanity?
        super(TestRunner, self).__init__(**options)
        # uid to resource, in definition order
        self._test_metadata: List[Any] = []
        self._tests: MutableMapping[str, str] = OrderedDict()
        self.result.report = TestReport(
            name=self.cfg.name,
            description=self.cfg.description,
            uid=self.cfg.name,
            timeout=self.cfg.timeout,
            label=self.cfg.label,
            information=[("testplan_version", self.get_testplan_version())],
        )
        self._exporters: Optional[List[BaseExporter]] = None
        self._web_server_thread: Any = None
        self._file_log_handler: Optional[Any] = None
        self._configure_stdout_logger()
        # Before saving test report, recursively generate unique strings in
        # uuid4 format as report uid instead of original one. Skip this step
        # when executing unit/functional tests or running in interactive mode.
        self._reset_report_uid = not self._is_interactive_run()
        self.scheduled_modules: List[
            Tuple[str, str]
        ] = []  # For interactive reload
        self.remote_services: Dict[str, "RemoteService"] = {}
        self.runid_filename: str = uuid.uuid4().hex
        self.define_runpath()
        self.result.report.information.append(("runpath", self.runpath))
        self._archive_path: str
        self._define_archive_path()
        self._runnable_uids: Set[str] = set()
        self._verified_targets: Dict[
            int, str
        ] = {}  # target object id -> runnable uid
        self.resource_monitor_server: Optional["ResourceMonitorServer"] = None
        self.resource_monitor_server_file_path: str
        self.resource_monitor_client: Optional["ResourceMonitorClient"] = None

    def __str__(self) -> str:
        return f"Testplan[{self.uid()}]"

    @staticmethod
    def get_testplan_version() -> str:
        import testplan

        return testplan.__version__

    @property
    def report(self) -> TestReport:  # type: ignore[override]
        """Tests report."""
        return self.result.report

    @property
    def exporters(self) -> List[BaseExporter]:
        """
        Return a list of
        :py:class:`report exporters <testplan.exporters.testing.base.Exporter>`.
        """
        if self._exporters is None:
            self._exporters = self.get_default_exporters()
            if self.cfg.exporters:
                self._exporters.extend(self.cfg.exporters)
            for exporter in self._exporters:
                if hasattr(exporter, "cfg"):
                    exporter.cfg.parent = self.cfg
                exporter.parent = self  # type: ignore[attr-defined]
        return self._exporters

    def get_test_metadata(self) -> List[Any]:
        return self._test_metadata

    def disable_reset_report_uid(self) -> None:
        """Do not generate unique strings in uuid4 format as report uid"""
        self._reset_report_uid = False

    def get_default_exporters(self) -> List[BaseExporter]:
        """
        Instantiate certain exporters if related cmdline argument (e.g. --pdf)
        or programmatic arguments (e.g. pdf_path) is passed but there are not
        any exporter declarations.
        """
        exporters: List[BaseExporter] = []
        if self.cfg.pdf_path:
            exporters.append(test_exporters.PDFExporter())
        if self.cfg.report_tags or self.cfg.report_tags_all:
            exporters.append(test_exporters.TagFilteredPDFExporter())
        if self.cfg.json_path:
            exporters.append(test_exporters.JSONExporter())
        if self.cfg.xml_dir:
            exporters.append(test_exporters.XMLExporter())
        if self.cfg.http_url:
            exporters.append(test_exporters.HTTPExporter())
        if self.cfg.dump_failed_tests:
            exporters.append(test_exporters.FailedTestsExporter())
        if self.cfg.ui_port is not None:
            exporters.append(
                test_exporters.WebServerExporter(ui_port=self.cfg.ui_port)
            )
        if (
            not self._is_interactive_run()
            and self.cfg.tracing_tests is not None
        ):
            exporters.append(test_exporters.CoveredTestsExporter())
        return exporters

    def add_environment(
        self, env: EnvironmentCreator, resource: Optional[Environments] = None
    ) -> str:
        """
        Adds an environment to the target resource holder.

        :param env: Environment creator instance.
        :type env: Subclass of
            :py:class:`~testplan.environment.EnvironmentCreator`
        :param resource: Target environments holder resource.
        :type resource: Subclass of
            :py:class:`~testplan.environment.Environments`
        :return: Environment uid.
        :rtype: ``str``
        """
        target_resource: Any = (
            self.resources[resource]  # type: ignore[index]
            if resource
            else self.resources.environments
        )
        target = env.create(parent=self)
        env_uid: str = env.uid()
        target_resource.add(target, env_uid)
        return env_uid

    def add_resource(
        self, resource: Resource, uid: Optional[str] = None
    ) -> str:
        """
        Adds a test :py:class:`executor <testplan.runners.base.Executor>`
        resource in the test runner environment.

        :param resource: Test executor to be added.
        :param uid: Optional input resource uid. We now force its equality with
            resource's own uid.
        :return: Resource uid assigned.
        """
        resource.parent = self
        resource.cfg.parent = self.cfg
        if uid and uid != resource.uid():
            raise ValueError(
                f"Unexpected uid value ``{uid}`` received, mismatched with "
                f"Resource uid ``{resource.uid()}``"
            )
        return self.resources.add(resource, uid=uid)

    def add_exporters(self, exporters: List[Exporter]) -> None:
        """
        Add a list of
        :py:class:`report exporters <testplan.exporters.testing.base.Exporter>`
        for outputting test report.

        :param exporters: Test exporters to be added.
        :type exporters: ``list`` of :py:class:`~testplan.runners.base.Executor`
        """
        self.cfg.exporters.extend(get_exporters(exporters))

    def add_remote_service(self, remote_service: "RemoteService") -> None:
        """
        Adds a remote service
        :py:class:`~testplan.common.remote.remote_service.RemoteService`
        object to test runner.

        :param remote_service: RemoteService object
        :param remote_service:
            :py:class:`~testplan.common.remote.remote_service.RemoteService`
        """
        name = remote_service.cfg.name
        if name in self.remote_services:
            raise ValueError(f"Remove Service [{name}] already exists")

        remote_service.parent = self
        remote_service.cfg.parent = self.cfg
        self.remote_services[name] = remote_service

    def skip_step(self, step: Callable[..., Any]) -> bool:
        if isinstance(
            self.result.step_results.get("_start_remote_services", None),
            Exception,
        ):
            if step in (
                self._pre_exporters,
                self._invoke_exporters,
                self._post_exporters,
                self._stop_remote_services,
            ):
                return False
            return True
        return False

    def _start_remote_services(self) -> Optional[Exception]:
        for rmt_svc in self.remote_services.values():
            try:
                rmt_svc.start()
            except Exception as e:
                msg = traceback.format_exc()
                self.logger.error(msg)
                self.report.logger.error(msg)
                self.report.status_override = Status.ERROR
                # skip the rest, set step return value
                return e
        return None

    def _stop_remote_services(
        self,
    ) -> Optional[Union[Exception, ExceptionGroup]]:
        es = []
        for rmt_svc in self.remote_services.values():
            try:
                rmt_svc.stop()
            except Exception as e:
                msg = traceback.format_exc()
                self.logger.error(msg)
                # NOTE: rmt svc cannot be closed before report export due to
                # NOTE: rmt ref being used during report export, it's
                # NOTE: meaningless to update report obj here
                self.report.status_override = Status.ERROR
                es.append(e)
        if es:
            if len(es) > 1:
                return ExceptionGroup(
                    "multiple remote services failed to stop", es
                )
            return es[0]
        return None

    def _clone_task_for_part(
        self, task_info: TaskInformation, part_tuple: Tuple[int, int]
    ) -> TaskInformation:
        task_arguments = task_info.task_arguments
        task_arguments["part"] = part_tuple
        self.logger.debug(
            "Task re-created with arguments: %s",
            task_arguments,
        )

        # unfortunately it is not easy to clone a Multitest with some parameters changed
        # ideally we need just the part changed, but Multitests could not share Drivers,
        # so it could not be recreated from its configuration as then more than one
        # Multitest would own the same drivers. So here we recreating it from the task

        target = Task(**task_arguments)
        new_task_info = self._assemble_task_info(target)
        return new_task_info

    def _create_task_n_info(
        self,
        task_arguments: dict,
        num_of_parts: Union[int, "Literal['auto']", None] = None,
    ) -> TaskInformation:
        self.logger.debug(
            "Task created with arguments: %s",
            task_arguments,
        )
        task = Task(**task_arguments)
        task_info = self._assemble_task_info(
            task, task_arguments, num_of_parts
        )
        return task_info

    def discover(
        self,
        path: str = ".",
        name_pattern: Union[str, Pattern] = r".*\.py$",
    ) -> List[TestTask]:
        """
        Discover task targets under path in the modules that matches name pattern,
        and return the created Task object.

        :param path: the root path to start a recursive walk and discover,
            default is current directory.
        :param name_pattern: a regex pattern to match the file name.
        :return: A list of Task objects
        """

        self.logger.user_info(
            "Discovering task target with file name pattern '%s' under '%s'",
            name_pattern,
            path,
        )
        regex = re.compile(name_pattern)
        discovered: List[TaskInformation] = []

        for root, dirs, files in os.walk(path or "."):
            for filename in files:
                if not regex.match(filename):
                    continue

                filepath = os.path.join(root, filename)
                module = filename.split(".")[0]

                with import_tmp_module(module, root) as mod:
                    for attr in dir(mod):
                        target = getattr(mod, attr)
                        if not is_task_target(target):
                            continue

                        self.logger.debug(
                            "Discovered task target %s::%s", filepath, attr
                        )

                        target_info: TaskTargetInformation = (
                            target.__task_target_info__
                        )  # what user specifies in @task_target

                        task_arguments = dict(
                            target=attr,
                            module=module,
                            path=root,
                            **target_info.task_kwargs,
                        )

                        if target_info.target_params:
                            for param in target_info.target_params:
                                if isinstance(param, dict):
                                    task_arguments["args"] = None
                                    task_arguments["kwargs"] = param
                                elif isinstance(param, (tuple, list)):
                                    task_arguments["args"] = param
                                    task_arguments["kwargs"] = None
                                else:
                                    raise TypeError(
                                        "task_target's parameters can only"
                                        " contain dict/tuple/list, but"
                                        f" received: {param}"
                                    )
                                discovered.append(
                                    self._create_task_n_info(
                                        deepcopy(task_arguments),
                                        target_info.multitest_parts,  # type: ignore[arg-type]
                                    )
                                )
                        else:
                            discovered.append(
                                self._create_task_n_info(
                                    task_arguments,
                                    target_info.multitest_parts,  # type: ignore[arg-type]
                                )
                            )

        return [_attach_task_info(task_info) for task_info in discovered]

    def calculate_pool_size(self) -> None:
        """
        Calculate the right size of the pool based on the weight (runtime) of the tasks,
        so that runtime of all tasks meets the plan_runtime_target.
        """
        for executor in self.resources:
            if isinstance(executor, Pool) and executor.is_auto_size:
                pool_size = self.calculate_pool_size_by_tasks(
                    list(executor.added_items.values())
                )
                self.logger.user_info(
                    f"Set pool size to {pool_size} for {executor.cfg.name}"
                )
                executor.size = pool_size

    def calculate_pool_size_by_tasks(self, tasks: Collection[Task]) -> int:
        """
        Calculate the right size of the pool based on the weight (runtime) of the tasks,
        so that runtime of all tasks meets the plan_runtime_target.
        """
        if len(tasks) == 0:
            return 1

        _tasks = sorted(tasks, key=lambda task: task.weight, reverse=True)
        plan_runtime_target = self.cfg.plan_runtime_target

        if plan_runtime_target == "auto":
            self.logger.warning(
                "Update plan_runtime_target to %d", _tasks[0].weight
            )
            plan_runtime_target = _tasks[0].weight
        elif _tasks[0].weight > plan_runtime_target:
            for task in _tasks:
                if task.weight > plan_runtime_target:
                    self.logger.warning(
                        "%s weight %d is greater than plan_runtime_target %d",
                        task,
                        task.weight,
                        self.cfg.plan_runtime_target,
                    )
            self.logger.warning(
                "Update plan_runtime_target to %d", _tasks[0].weight
            )
            plan_runtime_target = _tasks[0].weight

        containers = [0]
        for task in _tasks:
            if task.weight:
                if min(containers) + task.weight <= plan_runtime_target:
                    containers[containers.index(min(containers))] += (
                        task.weight
                    )
                else:
                    containers.append(task.weight)
            else:
                containers.append(plan_runtime_target)
        return len(containers)

    def schedule(
        self,
        task: Optional[Task] = None,
        resource: Optional[str] = None,
        **options: Any,
    ) -> Optional[str]:
        """
        Schedules a serializable
        :py:class:`~testplan.runners.pools.tasks.base.Task` in a task runner
        :py:class:`~testplan.runners.pools.base.Pool` executor resource.

        :param task: Input task, if it is None, a new Task will be constructed
            using the options parameter.
        :type task: :py:class:`~testplan.runners.pools.tasks.base.Task`
        :param resource: Name of the target executor, which is usually a Pool,
            default value None indicates using local executor.
        :type resource: ``str`` or ``NoneType``
        :param options: Task input options.
        :type options: ``dict``
        :return uid: Assigned uid for task.
        :rtype: ``str`` or ``NoneType``
        """

        return self.add(task or Task(**options), resource=resource)

    def schedule_all(
        self,
        path: str = ".",
        name_pattern: Union[str, Pattern[str]] = r".*\.py$",
        resource: Optional[str] = None,
    ) -> None:
        """
        Discover task targets under path in the modules that matches name pattern,
        create task objects from them and schedule them to resource (usually pool)
        for execution.

        :param path: the root path to start a recursive walk and discover,
            default is current directory.
        :type path: ``str``
        :param name_pattern: a regex pattern to match the file name.
        :type name_pattern: ``str``
        :param resource: Name of the target executor, which is usually a Pool,
            default value None indicates using local executor.
        :type resource: ``str`` or ``NoneType``
        """

        tasks = self.discover(path=path, name_pattern=name_pattern)
        tasks = self.auto_part(tasks)
        for task in tasks:
            self.add(task, resource=resource)

    def auto_part(self, tasks: List[TestTask]) -> List[TestTask]:
        """
        Automatically partitions tasks into smaller parts based on runtime limits.
        This method takes a list of tasks and partitions them into smaller tasks
        if their runtime exceeds the configured `auto_part_runtime_limit`. The
        partitioning is determined by analyzing runtime data and calculating
        appropriate parts and weights for each task.

        If the `auto_part_runtime_limit` is set to "auto", the method derives the
        runtime limit based on historical runtime data or defaults to a predefined
        maximum value if no runtime data is available.

        :param tasks: List of tasks to be partitioned.
        :type tasks: List[Task]
        :return: List of partitioned tasks.
        :rtype: List[Task]
        """
        partitioned: List[TaskInformation] = []

        if self._is_interactive_run():
            self.logger.debug("Auto part is not supported in interactive mode")
            return tasks

        discovered: List[TaskInformation] = [
            _detach_task_info(task) for task in tasks
        ]
        runtime_data = self.cfg.runtime_data or {}
        self._adjust_runtime_data(discovered, runtime_data)
        # here we replace the original runtime data with adjusted values
        # and "previous" testcase count with current run count
        self.cfg.set_local("runtime_data", runtime_data)

        auto_part_runtime_limit = self._calculate_part_runtime(discovered)
        for task_info in discovered:
            partitioned.extend(
                self._calculate_parts_and_weights(
                    task_info, auto_part_runtime_limit
                )
            )

        return [_attach_task_info(task_info) for task_info in partitioned]

    def _adjust_runtime_data(
        self, discovered: List[TaskInformation], runtime_data: dict
    ) -> None:
        """
        Adjust the runtime data to ensure that all discovered tasks have their
        runtime data available. If a task's UID is not found in the runtime data,
        it will be added with default values.
        """
        for task_info in discovered:
            uid = task_info.uid
            time_info = runtime_data.get(uid, None)
            if time_info and isinstance(
                task_info.materialized_test, MultiTest
            ):
                prev_case_count = time_info.get("testcase_count", 0)
                # We need parts calculation to remain the same even with filters, so ignore all filters in this dry_run.
                # TODO: Consider filters to better split into parts? part numbers will no longer be the same if filters are considered.
                curr_case_count = task_info.materialized_test.dry_run(
                    with_filter=False
                ).report.counter["total"]  # type: ignore[attr-defined]
                time_info["testcase_count"] = curr_case_count
                if not curr_case_count:
                    time_info["execution_time"] = 0
                elif prev_case_count:
                    # XXX: lb defined, ub?
                    adjusted_exec_time = time_info["execution_time"] * max(
                        curr_case_count / prev_case_count,
                        MULTITEST_EXEC_TIME_ADJUST_FACTOR_LB,
                    )
                    self.logger.user_info(
                        "%s: adjust estimated total execution time %.2f -> %.2f "
                        "(prev total testcase number: %d, curr total testcase number: %d)",
                        uid,
                        time_info["execution_time"],
                        adjusted_exec_time,
                        prev_case_count,
                        curr_case_count,
                    )
                    time_info["execution_time"] = adjusted_exec_time

    def _calculate_part_runtime(
        self, discovered: List[TaskInformation]
    ) -> float:
        if self.cfg.auto_part_runtime_limit != "auto":
            return self.cfg.auto_part_runtime_limit  # type: ignore[no-any-return]

        runtime_data = self.cfg.runtime_data or {}
        if not runtime_data:
            self.logger.warning(
                "Cannot derive auto_part_runtime_limit without runtime data, "
                "set to default %s",
                defaults.AUTO_PART_RUNTIME_MAX,
            )
            return defaults.AUTO_PART_RUNTIME_MAX

        max_mt_start_stop = 0  # multitest
        max_ut_runtime = 0  # unit test

        for task_info in discovered:
            uid = task_info.uid
            time_info = runtime_data.get(uid, None)

            if time_info:
                if isinstance(task_info.materialized_test, MultiTest):
                    max_mt_start_stop = max(
                        max_mt_start_stop,
                        time_info["setup_time"] + time_info["teardown_time"],
                    )
                else:
                    max_ut_runtime = (
                        time_info["setup_time"]
                        + time_info["execution_time"]
                        + time_info["teardown_time"]
                    )

            else:
                self.logger.warning(
                    "Cannot find runtime data for %s, "
                    "set auto_part_runtime_limit to default %d",
                    uid,
                    defaults.AUTO_PART_RUNTIME_MAX,
                )
                return defaults.AUTO_PART_RUNTIME_MAX

        # by now we get all tasks setup/teardown time
        auto_part_runtime_limit = (
            max_mt_start_stop * defaults.START_STOP_FACTOR
        )
        auto_part_runtime_limit = min(
            max(auto_part_runtime_limit, defaults.AUTO_PART_RUNTIME_MIN),
            defaults.AUTO_PART_RUNTIME_MAX,
        )
        auto_part_runtime_limit = math.ceil(
            max(auto_part_runtime_limit, max_ut_runtime)
        )

        self.logger.user_info(
            "Set auto_part_runtime_limit to %s", auto_part_runtime_limit
        )
        return auto_part_runtime_limit

    def _calculate_parts_and_weights(
        self, task_info: TaskInformation, auto_part_runtime_limit: float
    ) -> List[TaskInformation]:
        num_of_parts = (
            task_info.num_of_parts
        )  # @task_target(multitest_parts=...)
        uid = task_info.uid
        runtime_data: dict = self.cfg.runtime_data or {}
        time_info: Optional[dict] = runtime_data.get(uid, None)

        partitioned: List[TaskInformation] = []

        if num_of_parts:
            if not isinstance(task_info.materialized_test, MultiTest):
                raise TypeError(
                    "multitest_parts specified in @task_target,"
                    " but the Runnable is not a MultiTest"
                )

            if num_of_parts == "auto":
                if not time_info:
                    self.logger.warning(
                        "%s parts is auto but cannot find it in runtime-data",
                        uid,
                    )
                    num_of_parts = 1
                else:
                    cap = min(
                        time_info["testcase_count"],
                        # the setup time shall take no more than 50% of runtime
                        math.ceil(
                            time_info["execution_time"]
                            / auto_part_runtime_limit
                            * 2
                        ),
                    )
                    cap = max(cap, 1)
                    formula = f"""
            num_of_parts = math.ceil(
                time_info["execution_time"] {time_info["execution_time"]}
                / (
                    self.cfg.auto_part_runtime_limit {auto_part_runtime_limit}
                    - time_info["setup_time"] {time_info["setup_time"]}
                    - time_info["teardown_time"] {time_info["teardown_time"]}
                )
            )
"""
                    try:
                        num_of_parts = math.ceil(
                            time_info["execution_time"]
                            / (
                                auto_part_runtime_limit
                                - time_info["setup_time"]
                                - time_info["teardown_time"]
                            )
                        )
                    except ZeroDivisionError:
                        self.logger.error(
                            f"ZeroDivisionError occurred when calculating num_of_parts for {uid}, set to 1. {formula}"
                        )
                        num_of_parts = 1

                    if num_of_parts < 1:
                        self.logger.error(
                            f"Calculated num_of_parts for {uid} is {num_of_parts}, set to 1. {formula}"
                        )
                        num_of_parts = 1

                    if num_of_parts > cap:
                        self.logger.error(
                            f"Calculated num_of_parts for {uid} is {num_of_parts} > cap {cap}, set to {cap}. {formula}"
                        )
                        num_of_parts = cap

            # by now we shall have a valid num_of_part, user specified or auto derived
            task_arguments = task_info.task_arguments
            if "weight" not in task_arguments:
                task_arguments["weight"] = (
                    math.ceil(
                        (time_info["execution_time"] / num_of_parts)
                        + time_info["setup_time"]
                        + time_info["teardown_time"]
                    )
                    if time_info
                    else int(auto_part_runtime_limit)
                )
            self.logger.user_info(
                "%s: parts=%d, weight=%d",
                uid,
                num_of_parts,
                task_arguments["weight"],
            )
            if not isinstance(task_info.target, Task):
                raise TypeError(
                    f"Expected Task, got {type(task_info.target)!r}"
                )
            if num_of_parts == 1:
                task_info.target.weight = task_arguments["weight"]
                partitioned.append(task_info)
            else:
                for i in range(num_of_parts):
                    part_tuple = (i, num_of_parts)
                    new_task_info = self._clone_task_for_part(
                        task_info, part_tuple
                    )
                    partitioned.append(new_task_info)

        else:
            if not isinstance(task_info.target, Task):
                raise TypeError(
                    f"Expected Task, got {type(task_info.target)!r}"
                )
            if time_info and not task_info.target.weight:
                task_info.target.weight = math.ceil(
                    time_info["execution_time"]
                    + time_info["setup_time"]
                    + time_info["teardown_time"]
                )
            if task_info.target.weight:
                self.logger.user_info(
                    "%s: weight=%d", uid, task_info.target.weight
                )
            partitioned.append(task_info)

        return partitioned

    def add(
        self,
        target: Union[Test, Task, Callable],
        resource: Optional[str] = None,
    ) -> Optional[str]:
        """
        Adds a :py:class:`runnable <testplan.common.entity.base.Runnable>`
        test entity, or a :py:class:`~testplan.runners.pools.tasks.base.Task`,
        or a callable that returns a test entity to a
        :py:class:`~testplan.runners.base.Executor` resource.

        :param target: Test target.
        :type target: :py:class:`~testplan.common.entity.base.Runnable` or
            :py:class:`~testplan.runners.pools.tasks.base.Task` or ``callable``
        :param resource: Name of the target executor, which is usually a Pool,
            default value None indicates using local executor.
        :type resource: ``str`` or ``NoneType``
        :return: Assigned uid for test.
        :rtype: ``str`` or ```NoneType``
        """

        # Get the real test entity and verify if it should be added
        task_info = self._assemble_task_info(target)
        self._verify_task_info(task_info)
        uid = task_info.uid

        # let see if it is filtered
        if not self._should_task_running(task_info):
            return None

        # "--list" option always means not executing tests
        lister: Lister = self.cfg.test_lister
        if lister is not None and not lister.metadata_based:
            self.cfg.test_lister.log_test_info(task_info.materialized_test)
            return None

        if resource is None or self._is_interactive_run():
            # use local runner for interactive
            resource = self.resources.first()
            # just enqueue the materialized test
            target = task_info.materialized_test
        else:
            target = task_info.target

        if self._is_interactive_run():
            self._register_task_for_interactive(task_info)

        self._register_task(
            resource, target, uid, task_info.materialized_test.get_metadata()
        )
        return uid

    def _is_interactive_run(self) -> bool:
        return self.cfg.interactive_port is not None

    def _register_task(
        self, resource: str, target: TestTask, uid: str, metadata: Any
    ) -> None:
        self._tests[uid] = resource
        self._test_metadata.append(metadata)
        self.resources[resource].add(target, uid)  # type: ignore[attr-defined]

    def _assemble_task_info(
        self,
        target: TestTask,
        task_arguments: Optional[dict] = None,
        num_of_parts: Union[None, int, Literal["auto"]] = None,
    ) -> TaskInformation:
        if isinstance(target, Task):
            if hasattr(target, CACHED_TASK_INFO_ATTRIBUTE):
                task_info = _detach_task_info(target)
                return task_info
            else:
                materialized_test = target.materialize()
        elif isinstance(target, Test):
            materialized_test = target
        elif callable(target):
            materialized_test = target()
        else:
            raise TypeError(
                "Unrecognized test target of type {}".format(type(target))
            )

        # TODO: include executor in ancestor chain?
        if isinstance(materialized_test, Runnable):
            materialized_test.parent = self
            materialized_test.cfg.parent = self.cfg

        uid = materialized_test.uid()

        # Reset the task uid which will be used for test result transport in
        # a pool executor, it makes logging or debugging easier.

        # TODO: This mutating target should we do a copy?
        if isinstance(target, Task):
            target._uid = uid

        return TaskInformation(
            target, materialized_test, uid, task_arguments or {}, num_of_parts
        )

    def _register_task_for_interactive(
        self, task_info: TaskInformation
    ) -> None:
        target = task_info.target
        if isinstance(target, Task) and isinstance(target._target, str):
            self.scheduled_modules.append(
                (
                    target._module or target._target.rsplit(".", 1)[0],
                    os.path.abspath(target._path),
                )
            )

    def _verify_task_info(self, task_info: TaskInformation) -> None:
        uid = task_info.uid
        if uid in self._tests:
            raise ValueError(
                '{} with uid "{}" already added.'.format(self._tests[uid], uid)
            )

        if uid in self._runnable_uids:
            raise RuntimeError(
                f"Runnable with uid {uid} has already been verified"
            )
        else:
            #  TODO: this should be part of the add
            self._runnable_uids.add(uid)

    def _should_task_running(self, task_info: TaskInformation) -> bool:
        should_run = True
        if type(self.cfg.test_filter) is not filtering.Filter:
            test = task_info.materialized_test
            should_run = test.should_run()
            self.logger.debug(
                "Should run %s? %s",
                test.name,
                "Yes" if should_run else "No",
            )

        return should_run

    def _check_pidfile(self) -> None:
        """
        Check if a PID file exists and verify if another testplan instance is using this runpath.

        For remote processes (PID file format: {host}:{port};{pid}), verifies the SSH connection
        is still active by checking for an ESTABLISHED TCP connection to the specified host:port.

        For local processes (PID file format: {pid}), checks if the process is still running.

        Raises RunpathInUseError if another active testplan instance is detected.
        """

        if not os.path.exists(self._pidfile_path):
            return

        with open(self._pidfile_path, "r") as pid_file:
            pid_file_content = pid_file.read().strip().split(";")

        host: Optional[str] = None
        port: Optional[str] = None
        if len(pid_file_content) == 1:
            pid = pid_file_content[0]
        elif len(pid_file_content) == 2:
            connection_info, pid = pid_file_content
            if ":" in connection_info:
                host, port = connection_info.rsplit(":", 1)
            else:
                return
        else:
            return

        if pid and pid.isdigit():
            if (
                host
                and port is not None
                and port.isdigit()
                and self._is_remote_process_alive(host, int(port))
            ):
                raise RunpathInUseError(
                    f"Another testplan instance on {host} (PID: {pid}) is already using runpath: {self._runpath}"
                )
            else:
                pid_int = int(pid)
                if psutil.pid_exists(pid_int) and pid_int != os.getpid():
                    raise RunpathInUseError(
                        f"Another testplan instance with PID {pid_int} is already using runpath: {self._runpath}"
                    )

    def _is_remote_process_alive(self, host: str, port: int) -> bool:
        """
        Check if a remote process is alive by verifying the SSH connection
        is still active.
        """
        try:
            ipaddress.ip_address(host)
        except ValueError:
            return False

        for conn in psutil.net_connections(kind="tcp"):
            if (
                conn.status == psutil.CONN_ESTABLISHED
                and conn.raddr
                and conn.raddr.ip == host
                and conn.raddr.port == port
            ):
                return True

        return False

    def make_runpath_dirs(self) -> None:
        """
        Creates runpath related directories.
        """
        if self._runpath is None:
            raise RuntimeError(
                "{} runpath cannot be None".format(self.__class__.__name__)
            )

        self._pidfile_path = os.path.join(self._runpath, "testplan.pid")
        self._check_pidfile()

        self.logger.user_info(
            "Testplan[%s] has runpath: %s and pid %s",
            self.cfg.name,
            self._runpath,
            os.getpid(),
        )

        self._scratch = os.path.join(self._runpath, "scratch")

        if self.cfg.path_cleanup is False:
            makedirs(self._runpath)
            makedirs(self._scratch)
        else:
            makeemptydirs(self._runpath)
            makeemptydirs(self._scratch)

        with open(self._pidfile_path, "w") as pid_file:
            pid_file.write(str(os.getpid()))

        with open(
            os.path.join(self._runpath, self.runid_filename), "wb"
        ) as fp:
            pass

        if self.cfg.resource_monitor:
            self.resource_monitor_server_file_path = os.path.join(
                self.scratch, "resource_monitor"
            )
            makedirs(self.resource_monitor_server_file_path)

        if not os.environ.get("MPLCONFIGDIR"):
            os.environ["MPLCONFIGDIR"] = os.path.join(
                self._runpath, "matplotlib"
            )

    def _start_resource_monitor(self) -> None:
        """Start resource monitor server and client"""
        from testplan.monitor.resource import (
            ResourceMonitorClient,
            ResourceMonitorServer,
        )

        if self.cfg.resource_monitor:
            self.resource_monitor_server = ResourceMonitorServer(
                self.resource_monitor_server_file_path,
                detailed=self.cfg.logger_level == logger.DEBUG,
            )
            self.resource_monitor_server.start()
            self.resource_monitor_client = ResourceMonitorClient(
                self.resource_monitor_server.address, is_local=True
            )
            self.resource_monitor_client.start()

    def _stop_resource_monitor(self) -> None:
        """Stop resource monitor server and client"""
        if self.resource_monitor_client:
            self.resource_monitor_client.stop()
            self.resource_monitor_client = None
        if self.resource_monitor_server:
            self.resource_monitor_server.stop()
            self.resource_monitor_server = None

    def _define_archive_path(self) -> None:
        if not self.cfg.archive_runpath:
            return
        archive_dir = os.path.abspath(
            os.path.expandvars(os.path.expanduser(self.cfg.archive_runpath))
        )
        timestamp = time.strftime("%Y%m%d-%H%M%S")
        self._archive_path = os.path.join(
            archive_dir,
            f"{os.path.basename(self.runpath)}_{timestamp}.tar.zst",
        )
        self.result.report.information.append(
            ("runpath_archive", self._archive_path)
        )

    def _archive_runpath(self) -> None:
        """
        Archive the runpath to a user specified directory.
        """
        if not self.cfg.archive_runpath:
            return

        if self.result.report.passed:
            self.logger.user_info("Testplan passed, skipping runpath archive")
            return

        archive_dir = os.path.dirname(self._archive_path)
        if not os.path.exists(archive_dir):
            os.makedirs(archive_dir, exist_ok=True)

        if not os.path.exists(self.runpath):
            self.logger.error(
                f"Runpath {self.runpath} does not exist, cannot archive."
            )
            return

        self.logger.user_info(
            f"Archiving runpath {self.runpath} to {self._archive_path}"
        )

        with open(self._archive_path, "wb") as f:
            cctx = zstd.ZstdCompressor(level=3, threads=-1)
            with cctx.stream_writer(f) as compressor:
                with tarfile.open(fileobj=compressor, mode="w|") as tar:
                    tar.add(
                        self.runpath, arcname=os.path.basename(self.runpath)
                    )

        self.logger.user_info(f"Runpath archived to {self._archive_path}")

    def _remove_pidfile(self) -> None:
        """
        Remove the PID file after testplan finishes.

        Prevents stale PID files from causing false RunpathInUseError on
        subsequent runs when OS PID recycling reassigns the old PID to an
        unrelated process.
        """
        pidfile_path = getattr(self, "_pidfile_path", None)
        if not pidfile_path or not os.path.exists(pidfile_path):
            return
        try:
            with open(pidfile_path, "r") as f:
                pid = f.read().strip()
            if pid == str(os.getpid()):
                os.remove(pidfile_path)
        except OSError:
            pass

    def add_pre_resource_steps(self) -> None:
        """Runnable steps to be executed before resources started."""
        self._add_step(self.timer.start, "run")
        super(TestRunner, self).add_pre_resource_steps()
        self._add_step(self._start_remote_services)
        self._add_step(self.make_runpath_dirs)
        self._add_step(self._configure_file_logger)
        self._add_step(self.calculate_pool_size)
        self._add_step(self._start_resource_monitor)

    def add_main_batch_steps(self) -> None:
        """Runnable steps to be executed while resources are running."""
        self._add_step(self._wait_ongoing)

    def add_post_resource_steps(self) -> None:
        """Runnable steps to be executed after resources stopped."""
        super(TestRunner, self).add_post_resource_steps()
        self._add_step(self._create_result)
        self._add_step(self._log_test_status)
        self._add_step(self.timer.end, "run")  # needs to happen before export
        self._add_step(self._pre_exporters)
        self._add_step(self._invoke_exporters)
        self._add_step(self._post_exporters)
        self._add_step(self._stop_remote_services)
        self._add_step(self._stop_resource_monitor)
        self._add_step(self._archive_runpath)
        self._add_step(self._remove_pidfile)

    def _collect_timeout_info(self) -> None:
        threads, processes = self._get_process_info(recursive=True)
        self._timeout_info: Dict[str, List[str]] = {
            "threads": [],
            "processes": [],
        }
        for thread in threads:
            self._timeout_info["threads"].append(
                os.linesep.join(
                    [thread.name]
                    + format_stack(sys._current_frames()[thread.ident])  # type: ignore[index]
                )
            )

        for process in processes:
            command = " ".join(process.cmdline()) or process
            parent_pid = getattr(process, "ppid", lambda: None)()
            self._timeout_info["processes"].append(
                f"Pid: {process.pid}, Parent pid: {parent_pid}, {command}"
            )

    def _wait_ongoing(self) -> None:
        # TODO: if a pool fails to initialize we could reschedule the tasks.
        if self.resources.start_exceptions:
            for resource, exception in self.resources.start_exceptions.items():
                self.logger.critical(
                    "Aborting %s due to start exception", resource
                )
                resource.abort()

        _start_ts = time.time()

        while self.active:
            if self.cfg.timeout and time.time() - _start_ts > self.cfg.timeout:
                msg = f"Timeout: Aborting execution after {self.cfg.timeout} seconds"
                self.report.logger.error(msg)
                self.logger.error(msg)
                self._collect_timeout_info()

                # Abort resources e.g pools
                for dep in self.abort_dependencies():
                    self._abort_entity(dep)
                break

            pending_work = False
            for resource in self.resources:
                # Check if any resource has pending work.
                # Maybe print periodically the pending work of resource.
                pending_work = resource.pending_work() or pending_work

                # Poll the resource's health - if it has unexpectedly died
                # then abort the entire test to avoid hanging.
                if not resource.is_alive:
                    self.report.status_override = Status.ERROR
                    self.logger.critical(
                        "Aborting %s - %s unexpectedly died", self, resource
                    )
                    self.abort()

            if pending_work is False:
                break
            time.sleep(self.cfg.active_loop_sleep)

    def _post_run_checks(self, start_threads: Any, start_procs: Any) -> None:
        super()._post_run_checks(start_threads, start_procs)
        self._close_file_logger()

    def _create_result(self) -> bool:
        """Fetch task result from executors and create a full test result."""
        step_result = True
        test_results = self.result.test_results
        plan_report = self.result.report

        for uid, resource in self._tests.items():
            if not isinstance(self.resources[resource], Executor):
                continue

            resource_result = self.resources[resource].results.get(uid)  # type: ignore[attr-defined]
            # Tasks may not been executed (i.e. timeout), although the thread
            # will wait for a buffer period until the follow up work finishes.
            # But for insurance we assume that still some uids are missing.
            if not resource_result:
                continue
            elif isinstance(resource_result, TaskResult):
                if resource_result.result is None:
                    test_results[uid] = result_for_failed_task(resource_result)
                else:
                    test_results[uid] = resource_result.result
            else:
                test_results[uid] = resource_result

            run = test_results[uid].run
            report: Any = test_results[uid].report

            plan_report.append(report)
            step_result = step_result and run is True  # boolean or exception

        if hasattr(self, "_timeout_info"):
            msg = f"Testplan timed out after {self.cfg.timeout} seconds"
            timeout_entry = TestGroupReport(
                name="Testplan timeout",
                description=msg,
                category=ReportCategories.SYNTHESIZED,
                # status_override=Status.ERROR,
            )
            timeout_case = TestCaseReport(
                name="Testplan timeout",
                description=msg,
                status_override=Status.ERROR,
            )

            log_result = Result()
            log_result.log(
                message=f"".join(
                    f"{log['created'].strftime('%Y-%m-%d %H:%M:%S')} {log['levelname']} {log['message']}\n"
                    for log in self.report.flattened_logs
                ),
                description="Logs from testplan",
            )
            log_result.log(
                message=os.linesep.join(self._timeout_info["threads"]),
                description="Stack trace from threads",
            )
            log_result.log(
                message=os.linesep.join(self._timeout_info["processes"])
                if len(self._timeout_info["processes"])
                else "No child processes",
                description="Running child processes",
            )

            timeout_case.extend(log_result.serialized_entries)
            timeout_entry.append(timeout_case)
            plan_report.append(timeout_entry)

        # Reset UIDs of the test report and all of its children in UUID4 format
        if self._reset_report_uid:
            plan_report.reset_uid()

        return step_result

    def uid(self) -> str:
        """Entity uid."""
        return self.cfg.name  # type: ignore[no-any-return]

    def _log_test_status(self) -> None:
        if not self.report.entries:
            self.logger.warning(
                "No tests were run - check your filter patterns."
            )
        else:
            self.logger.log_test_status(self.cfg.name, self.report.status)

    def _pre_exporters(self) -> None:
        # Apply report filter if one exists
        if self.cfg.reporting_exclude_filter is not None:
            self.result.report = self.cfg.reporting_exclude_filter(self.report)

        # Attach resource monitor data
        if self.resource_monitor_server:
            self.report.resource_meta_path = (
                self.resource_monitor_server.dump()
            )

    def _invoke_exporters(self) -> None:
        if self.report.is_empty():  # skip empty report
            return

        if hasattr(self.report, "bubble_up_attachments"):
            self.report.bubble_up_attachments()

        export_context = ExportContext()
        for exporter in self.exporters:
            if isinstance(exporter, test_exporters.Exporter):
                run_exporter(
                    exporter=exporter,
                    source=self.report,
                    export_context=export_context,
                )
            else:
                raise NotImplementedError(
                    "Exporter logic not implemented for: {}".format(
                        type(exporter)
                    )
                )

        self.result.exporter_results = export_context.results

    def _post_exporters(self) -> None:
        # View report in web browser if "--browse" specified
        report_urls = []
        report_opened = False

        if self.report.is_empty():  # skip empty report
            self.logger.warning("Empty report, nothing to be exported!")
            return

        for result in self.result.exporter_results:
            report_url = getattr(result.exporter, "report_url", None)
            if report_url:
                report_urls.append(report_url)
                web_server_thread = getattr(
                    result.exporter, "web_server_thread", None
                )
                if web_server_thread:
                    # Keep an eye on this thread from `WebServerExporter`
                    # which will be stopped on Testplan abort
                    self._web_server_thread = web_server_thread
                    # Give priority to open report from local server
                    if self.cfg.browse and not report_opened:
                        webbrowser.open(report_url)
                        report_opened = True
                    # Stuck here waiting for web server to terminate
                    web_server_thread.join()

        if self.cfg.browse and not report_opened:
            if len(report_urls) > 0:
                for report_url in report_urls:
                    webbrowser.open(report_url)
            else:
                self.logger.warning(
                    "No reports opened, could not find "
                    "an exported result to browse"
                )

    def discard_pending_tasks(
        self,
        exec_selector: SExpr,
        report_status: Status = Status.INCOMPLETE,
        report_reason: str = "",
    ) -> None:
        for k, v in self.resources.items():
            if isinstance(v, Executor) and apply_single(exec_selector, k):
                v.discard_pending_tasks(report_status, report_reason)

    def abort_dependencies(self) -> Generator[Any, None, None]:
        """
        Yield all dependencies to be aborted before self abort.
        """
        if self._ihandler is not None:
            yield self._ihandler
        yield from super(TestRunner, self).abort_dependencies()

    def aborting(self) -> None:
        """Stop the web server if it is running."""
        if self._web_server_thread is not None:
            self._web_server_thread.stop()
        # XXX: to be refactored after aborting logic implemented for rmt svcs
        self._stop_remote_services()
        self._stop_resource_monitor()
        self._close_file_logger()

    def _configure_stdout_logger(self) -> None:
        """Configure the stdout logger by setting the required level."""
        logger.STDOUT_HANDLER.setLevel(self.cfg.logger_level)

    def _configure_file_logger(self) -> None:
        """
        Configure the file logger to the specified log levels. A log file
        will be created under the runpath (so runpath must be created before
        this method is called).
        """
        if self._runpath is None:
            raise RuntimeError(
                "Need to set up runpath before configuring logger"
            )

        if self.cfg.file_log_level is None:
            self.logger.debug("Not enabling file logging")
        else:
            self._file_log_handler = logger.configure_file_logger(
                self.cfg.file_log_level, self.runpath
            )

    def _close_file_logger(self) -> None:
        """
        Closes the file logger, releasing all file handles. This is necessary to
        avoid permissions errors on Windows.
        """
        if self._file_log_handler is not None:
            self._file_log_handler.flush()
            self._file_log_handler.close()
            logger.TESTPLAN_LOGGER.removeHandler(self._file_log_handler)
            self._file_log_handler = None

    def _run_batch_steps(self) -> None:
        if not self._tests:
            self.logger.warning("No tests were added, skipping execution!")
            self.status.change(self.STATUS.RUNNING)
            self.status.change(self.STATUS.FINISHED)
        else:
            super()._run_batch_steps()

    def run(self) -> TestRunnerResult:
        """
        Executes the defined steps and populates the result object.
        """
        if self.cfg.test_lister:
            self.result.run = True
            return self.result

        with tracing.attach_to_root_context():
            super().run()
            return self.result
