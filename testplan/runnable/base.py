"""Tests runner module."""
import datetime
import inspect
import math
import os
import random
import re
import time
import uuid
import webbrowser
from collections import OrderedDict
from dataclasses import dataclass
from typing import (
    Any,
    Callable,
    Collection,
    Dict,
    List,
    MutableMapping,
    Optional,
    Pattern,
    Tuple,
    Union,
)

import pytz
from schema import And, Or, Use

from testplan import defaults
from testplan.common.config import ConfigOption
from testplan.common.entity import (
    Runnable,
    RunnableConfig,
    RunnableResult,
    RunnableStatus,
)
from testplan.common.exporters import BaseExporter, ExportContext, run_exporter
from testplan.common.remote.remote_service import RemoteService
from testplan.common.report import MergeError
from testplan.common.utils import logger, strings
from testplan.common.utils.package import import_tmp_module
from testplan.common.utils.path import default_runpath, makedirs, makeemptydirs
from testplan.environment import EnvironmentCreator, Environments
from testplan.exporters import testing as test_exporters
from testplan.exporters.testing.base import Exporter
from testplan.report import (
    ReportCategories,
    Status,
    TestGroupReport,
    TestReport,
)
from testplan.report.filter import ReportingFilter
from testplan.report.testing.styles import Style
from testplan.runnable.interactive import TestRunnerIHandler
from testplan.runners.base import Executor
from testplan.runners.pools.base import Pool
from testplan.runners.pools.tasks import Task, TaskResult
from testplan.runners.pools.tasks.base import (
    TaskTargetInformation,
    get_task_target_information,
    is_task_target,
)
from testplan.testing import filtering, listing, ordering, tagging
from testplan.testing.base import Test, TestResult
from testplan.testing.common import TEST_PART_PATTERN_FORMAT_STRING
from testplan.testing.listing import Lister
from testplan.testing.multitest import MultiTest

TestTask = Union[Test, Task, Callable]


@dataclass
class TaskInformation:
    target: TestTask
    materialized_test: Test
    uid: str


def get_exporters(values):
    """
    Validation function for exporter declarations.

    :param values: Single or a list of exporter declaration(s).
    :return: List of initialized exporter objects.
    """

    def get_exporter(value):
        if isinstance(value, BaseExporter):
            return value
        elif isinstance(value, tuple):
            exporter_cls, params = value
            return exporter_cls(**params)
        raise TypeError("Invalid exporter value: {}".format(value))

    if values is None:
        return []
    elif isinstance(values, list):
        return [get_exporter(v) for v in values]
    return [get_exporter(values)]


def result_for_failed_task(original_result):
    """
    Create a new result entry for invalid result retrieved from a resource.
    """
    result = TestResult()
    result.report = TestGroupReport(
        name=str(original_result.task), category=ReportCategories.ERROR
    )
    attrs = [attr for attr in original_result.task.serializable_attrs]
    result_lines = [
        "{}: {}".format(attr, getattr(original_result.task, attr))
        if getattr(original_result.task, attr, None)
        else ""
        for attr in attrs
    ]
    result.report.logger.error(
        os.linesep.join([line for line in result_lines if line])
    )
    result.report.logger.error(original_result.reason)
    result.report.status_override = Status.ERROR
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


class TestRunnerConfig(RunnableConfig):
    """
    Configuration object for
    :py:class:`~testplan.runnable.TestRunner` runnable object.
    """

    ignore_extra_keys = True

    @classmethod
    def get_options(cls):
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
            ConfigOption("pdf_style", default=defaults.PDF_STYLE): Style,
            ConfigOption("report_tags", default=[]): [
                Use(tagging.validate_tag_value)
            ],
            ConfigOption("report_tags_all", default=[]): [
                Use(tagging.validate_tag_value)
            ],
            ConfigOption("merge_scheduled_parts", default=False): bool,
            ConfigOption("browse", default=False): bool,
            ConfigOption("ui_port", default=None): Or(None, int),
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
            # active_loop_sleep impacts cpu usage in interactive mode
            ConfigOption("active_loop_sleep", default=0.05): float,
            ConfigOption(
                "interactive_handler", default=TestRunnerIHandler
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
            ConfigOption("reporting_filter", default=None): Or(
                And(str, Use(ReportingFilter.parse)), None
            ),
            ConfigOption("xfail_tests", default=None): Or(dict, None),
            ConfigOption("runtime_data", default={}): Or(dict, None),
            ConfigOption(
                "auto_part_runtime_limit",
                default=defaults.AUTO_PART_RUNTIME_LIMIT,
            ): Or(int, float),
            ConfigOption(
                "plan_runtime_target", default=defaults.PLAN_RUNTIME_TARGET
            ): Or(int, float),
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

    def __init__(self):
        super(TestRunnerResult, self).__init__()
        self.test_results = OrderedDict()
        self.exporter_results = []
        self.test_report = None

    @property
    def report(self):
        """Tests report."""
        return self.test_report

    @property
    def success(self):
        """Run was successful."""
        return not self.test_report.failed and all(
            [
                exporter_result.success
                for exporter_result in self.exporter_results
            ]
        )


CACHED_TASK_INFO_ATTRIBUTE = "_cached_task_info"


def _cache_task_info(task_info: TaskInformation):
    task = task_info.target
    setattr(task, CACHED_TASK_INFO_ATTRIBUTE, task_info)
    return task


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
    :param merge_scheduled_parts: Merge report of scheduled MultiTest parts.
    :type merge_scheduled_parts: ``bool``
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
        `TestRunnerIHandler <testplan.runnable.interactive.TestRunnerIHandler>`
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
    :type auto_part_runtime_limit: ``int`` or ``float``
    :param plan_runtime_target: The testplan total runtime limitation for smart schedule
    :type plan_runtime_target: ``int`` or ``float``

    Also inherits all
    :py:class:`~testplan.common.entity.base.Runnable` options.
    """

    CONFIG = TestRunnerConfig
    STATUS = TestRunnerStatus
    RESULT = TestRunnerResult

    def __init__(self, **options):
        super(TestRunner, self).__init__(**options)
        # uid to resource, in definition order
        self._test_metadata = []
        self._tests: MutableMapping[str, str] = OrderedDict()
        self._result.test_report = TestReport(
            name=self.cfg.name,
            description=self.cfg.description,
            uid=self.cfg.name,
            timeout=self.cfg.timeout,
            label=self.cfg.label,
        )
        self._exporters = None
        self._web_server_thread = None
        self._file_log_handler = None
        self._configure_stdout_logger()
        # Before saving test report, recursively generate unique strings in
        # uuid4 format as report uid instead of original one. Skip this step
        # when executing unit/functional tests or running in interactive mode.
        self._reset_report_uid = not self._is_interactive_run()
        self.scheduled_modules = []  # For interactive reload
        self.remote_services = {}
        self.runid_filename = uuid.uuid4().hex
        self.define_runpath()
        self._runnable_uids = set()
        self._verified_targets = {}  # target object id -> runnable uid

    def __str__(self):
        return f"Testplan[{self.uid()}]"

    @property
    def report(self) -> TestReport:
        """Tests report."""
        return self._result.test_report

    @property
    def exporters(self):
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
                exporter.parent = self
        return self._exporters

    def get_test_metadata(self):
        return self._test_metadata

    def disable_reset_report_uid(self):
        """Do not generate unique strings in uuid4 format as report uid"""
        self._reset_report_uid = False

    def get_default_exporters(self):
        """
        Instantiate certain exporters if related cmdline argument (e.g. --pdf)
        or programmatic arguments (e.g. pdf_path) is passed but there are not
        any exporter declarations.
        """
        exporters = []
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
    ):
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
        resource = (
            self.resources[resource]
            if resource
            else self.resources.environments
        )
        target = env.create(parent=self)
        env_uid = env.uid()
        resource.add(target, env_uid)
        return env_uid

    def add_resource(
        self, resource: Executor, uid: Optional[str] = None
    ) -> str:
        """
        Adds a test :py:class:`executor <testplan.runners.base.Executor>`
        resource in the test runner environment.

        :param resource: Test executor to be added.
        :type resource: Subclass of :py:class:`~testplan.runners.base.Executor`
        :param uid: Optional input resource uid.
        :type uid: ``str`` or ``NoneType``
        :return: Resource uid assigned.
        :rtype:  ``str``
        """
        # NOTE: expose the config to the executors
        resource.parent = self
        resource.cfg.parent = self.cfg
        return self.resources.add(
            resource, uid=uid or getattr(resource, "uid", strings.uuid4)()
        )

    def add_exporters(self, exporters: List[Exporter]):
        """
        Add a list of
        :py:class:`report exporters <testplan.exporters.testing.base.Exporter>`
        for outputting test report.

        :param exporters: Test exporters to be added.
        :type exporters: ``list`` of :py:class:`~testplan.runners.base.Executor`
        """
        self.cfg.exporters.extend(get_exporters(exporters))

    def add_remote_service(self, remote_service: RemoteService):
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
        remote_service.start()

    def _stop_remote_services(self):

        for name, rmt_svc in self.remote_services.items():
            self.logger.info("Stopping Remote Server %s", name)
            rmt_svc.stop()

    def _clone_task_for_part(self, task_info, _task_arguments, part):
        _task_arguments["part"] = part
        self.logger.debug(
            "Task re-created with arguments: %s",
            _task_arguments,
        )

        # unfortunately it is not easy to clone a Multitest with some parameters changed
        # ideally we need just the part changed, but Multitests could not share Drivers,
        # so it could not be recreated from its configuration as then more than one
        # Multitest would own the same drivers. So here we recreating it from the task

        target = Task(**_task_arguments)
        new_task = self._collect_task_info(target)
        return new_task

    def _get_tasks(
        self, _task_arguments, num_of_parts, runtime_data
    ) -> List[TaskInformation]:
        self.logger.debug(
            "Task created with arguments: %s",
            _task_arguments,
        )
        task = Task(**_task_arguments)
        task_info = self._collect_task_info(task)

        uid = task_info.uid

        tasks: List[TaskInformation] = []
        time_info = runtime_data.get(uid, None)
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
                    num_of_parts = math.ceil(
                        time_info["execution_time"]
                        / (
                            self.cfg.auto_part_runtime_limit
                            - time_info["setup_time"]
                        )
                    )
                    if num_of_parts < 1:
                        raise RuntimeError(
                            f"Calculated num_of_parts for {uid} is {num_of_parts},"
                            " check the input runtime_data and auto_part_runtime_limit"
                        )
            if "weight" not in _task_arguments:
                _task_arguments["weight"] = (
                    math.ceil(
                        (time_info["execution_time"] / num_of_parts)
                        + time_info["setup_time"]
                    )
                    if time_info
                    else self.cfg.auto_part_runtime_limit
                )
            self.logger.user_info(
                "%s: parts=%d, weight=%d",
                uid,
                num_of_parts,
                _task_arguments["weight"],
            )
            if num_of_parts == 1:
                task_info.target.weight = _task_arguments["weight"]
                tasks.append(task_info)
            else:
                for i in range(num_of_parts):

                    part = (i, num_of_parts)
                    new_task = self._clone_task_for_part(
                        task_info, _task_arguments, part
                    )

                    tasks.append(new_task)

        else:
            if time_info and not task.weight:
                task_info.target.weight = math.ceil(
                    time_info["execution_time"] + time_info["setup_time"]
                )
                self.logger.user_info(
                    "%s: weight=%d", uid, task_info.target.weight
                )
            tasks.append(task_info)

        return tasks

    def discover(
        self,
        path: str = ".",
        name_pattern: Union[str, Pattern] = r".*\.py$",
    ) -> List[Task]:
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
        tasks: List[TaskInformation] = []

        runtime_data: dict = self.cfg.runtime_data or {}

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

                        task_target_info = get_task_target_information(target)
                        task_arguments = dict(
                            target=attr,
                            module=module,
                            path=root,
                            **task_target_info.task_kwargs,
                        )

                        multitest_parts = (
                            None
                            if self._is_interactive_run()
                            else task_target_info.multitest_parts
                        )

                        if task_target_info.target_params:
                            for param in task_target_info.target_params:
                                if isinstance(param, dict):
                                    task_arguments["args"] = None
                                    task_arguments["kwargs"] = param
                                elif isinstance(param, (tuple, list)):
                                    task_arguments["args"] = param
                                    task_arguments["kwargs"] = None
                                else:
                                    raise TypeError(
                                        f"task_target's parameters can only"
                                        " contain dict/tuple/list, but"
                                        " received: {param}"
                                    )
                                task_arguments["part"] = None
                                tasks.extend(
                                    self._get_tasks(
                                        task_arguments,
                                        multitest_parts,
                                        runtime_data,
                                    )
                                )
                        else:
                            tasks.extend(
                                self._get_tasks(
                                    task_arguments,
                                    multitest_parts,
                                    runtime_data,
                                )
                            )

        return [_cache_task_info(task_info) for task_info in tasks]

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
        plan_runtime_target = self.cfg.plan_runtime_target
        _tasks = sorted(tasks, key=lambda task: task.weight, reverse=True)
        if _tasks[0].weight > plan_runtime_target:
            for task in _tasks:
                if task.weight > plan_runtime_target:
                    self.logger.warning(
                        "%s weight %d is greater than plan_runtime_target %d",
                        task,
                        task.weight,
                        self.cfg.plan_runtime_target,
                    )
            self.logger.warning(
                "Update plan_runtime_weight to %d", _tasks[0].weight
            )
            plan_runtime_target = _tasks[0].weight

        containers = [0]
        for task in _tasks:
            if task.weight:
                if min(containers) + task.weight <= plan_runtime_target:
                    containers[
                        containers.index(min(containers))
                    ] += task.weight
                else:
                    containers.append(task.weight)
            else:
                containers.append(plan_runtime_target)
        return len(containers)

    def schedule(
        self,
        task: Optional[Task] = None,
        resource: Optional[str] = None,
        **options,
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
        name_pattern: Union[str, Pattern] = r".*\.py$",
        resource: Optional[str] = None,
    ):
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

        for task in tasks:
            self.add(task, resource=resource)

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
        task_info = self._collect_task_info(target)
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

    def _is_interactive_run(self):
        return self.cfg.interactive_port is not None

    def _register_task(self, resource, target, uid, metadata):
        self._tests[uid] = resource
        self._test_metadata.append(metadata)
        self.resources[resource].add(target, uid)

    def _collect_task_info(self, target: TestTask) -> TaskInformation:
        if isinstance(target, Test):
            target_test = target
        elif isinstance(target, Task):

            # First check if there is a cached task info
            # that is an optimization flow where task info
            # need to be created at discover, but the already defined api
            # need to pass Task, so we attach task_info to the task itself
            # and here we remove it
            if hasattr(target, CACHED_TASK_INFO_ATTRIBUTE):
                task_info = getattr(target, CACHED_TASK_INFO_ATTRIBUTE)
                setattr(target, CACHED_TASK_INFO_ATTRIBUTE, None)
                return task_info
            else:
                target_test = target.materialize()
        elif callable(target):
            target_test = target()
        else:
            raise TypeError(
                "Unrecognized test target of type {}".format(type(target))
            )

        if isinstance(target_test, Runnable):
            target_test.parent = self
            target_test.cfg.parent = self.cfg

        uid = target_test.uid()

        # Reset the task uid which will be used for test result transport in
        # a pool executor, it makes logging or debugging easier.

        # TODO: This mutating target should we do a copy?
        if isinstance(target, Task):
            target._uid = uid

        return TaskInformation(target, target_test, uid)

    def _register_task_for_interactive(self, task_info: TaskInformation):
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

    def _record_start(self):
        self.report.timer.start("run")

    def _record_end(self):
        self.report.timer.end("run")

    def make_runpath_dirs(self):
        """
        Creates runpath related directories.
        """
        if self._runpath is None:
            raise RuntimeError(
                "{} runpath cannot be None".format(self.__class__.__name__)
            )

        self.logger.user_info(
            "Testplan has runpath: %s and pid %s", self._runpath, os.getpid()
        )

        self._scratch = os.path.join(self._runpath, "scratch")

        if self.cfg.path_cleanup is False:
            makedirs(self._runpath)
            makedirs(self._scratch)
        else:
            makeemptydirs(self._runpath)
            makeemptydirs(self._scratch)

        with open(
            os.path.join(self._runpath, self.runid_filename), "wb"
        ) as fp:
            pass

    def pre_resource_steps(self):
        """Runnable steps to be executed before resources started."""
        super(TestRunner, self).pre_resource_steps()
        self._add_step(self._record_start)
        self._add_step(self.make_runpath_dirs)
        self._add_step(self._configure_file_logger)
        self._add_step(self.calculate_pool_size)

    def main_batch_steps(self):
        """Runnable steps to be executed while resources are running."""
        self._add_step(self._wait_ongoing)

    def post_resource_steps(self):
        """Runnable steps to be executed after resources stopped."""
        self._add_step(self._stop_remote_services)
        self._add_step(self._create_result)
        self._add_step(self._log_test_status)
        self._add_step(self._record_end)  # needs to happen before export
        self._add_step(self._pre_exporters)
        self._add_step(self._invoke_exporters)
        self._add_step(self._post_exporters)
        self._add_step(self._close_file_logger)
        super(TestRunner, self).post_resource_steps()

    def _wait_ongoing(self):
        # TODO: if a pool fails to initialize we could reschedule the tasks.
        if self.resources.start_exceptions:
            for resource, exception in self.resources.start_exceptions.items():
                self.logger.critical(
                    "Aborting %s due to start exception", resource
                )
                resource.abort()

        _start_ts = (
            self.result.test_report.timer["run"][0]
            - datetime.datetime(1970, 1, 1, tzinfo=pytz.utc)
        ).total_seconds()

        while self.active:
            if self.cfg.timeout and time.time() - _start_ts > self.cfg.timeout:
                msg = (
                    f"Timeout: Aborting execution after {self.cfg.timeout} seconds",
                )
                self.result.test_report.logger.error(msg)
                self.logger.error(msg)

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
                    self.result.test_report.status_override = Status.ERROR
                    self.logger.critical(
                        "Aborting %s - %s unexpectedly died", self, resource
                    )
                    self.abort()

            if pending_work is False:
                break
            time.sleep(self.cfg.active_loop_sleep)

    def _create_result(self):
        """Fetch task result from executors and create a full test result."""
        step_result = True
        test_results = self._result.test_results
        test_report = self._result.test_report
        test_rep_lookup = {}

        for uid, resource in self._tests.items():
            if not isinstance(self.resources[resource], Executor):
                continue

            resource_result = self.resources[resource].results.get(uid)
            # Tasks may not been executed (i.e. timeout), although the thread
            # will wait for a buffer period until the follow up work finishes.
            # But for insurance we assume that still some uids are missing.
            if not resource_result:
                continue
            elif isinstance(resource_result, TaskResult):
                if resource_result.status is False:
                    test_results[uid] = result_for_failed_task(resource_result)
                else:
                    test_results[uid] = resource_result.result
            else:
                test_results[uid] = resource_result

            run, report = test_results[uid].run, test_results[uid].report

            if report.part:
                if (
                    report.category != ReportCategories.TASK_RERUN
                    and self.cfg.merge_scheduled_parts
                ):
                    # Save the report temporarily and later will merge it
                    test_rep_lookup.setdefault(
                        report.definition_name, []
                    ).append((test_results[uid].run, report))
                    if report.definition_name not in test_report.entry_uids:
                        # Create a placeholder for merging sibling reports
                        if isinstance(resource_result, TaskResult):
                            # `runnable` must be an instance of MultiTest since
                            # the corresponding report has `part` defined. Can
                            # get a full structured report by `dry_run` and the
                            # order of testsuites/testcases can be retained.
                            runnable = resource_result.task.materialize()
                            runnable.parent = self
                            runnable.cfg.parent = self.cfg
                            runnable.unset_part()
                            report = runnable.dry_run().report

                        else:
                            report = report.__class__(
                                report.definition_name,
                                category=report.category,
                            )
                    else:
                        continue  # Wait all sibling reports collected

            test_report.append(report)
            step_result = step_result and run is True  # boolean or exception

        step_result = self._merge_reports(test_rep_lookup) and step_result

        # Reset UIDs of the test report and all of its children in UUID4 format
        if self._reset_report_uid:
            test_report.reset_uid()

        # Attach pool event into report
        for executor in self.resources:
            if isinstance(executor, Executor):
                self.report.add_event(executor.event_recorder)

        return step_result

    def _merge_reports(
        self, test_report_lookup: Dict[str, List[Tuple[bool, Any]]]
    ):
        """
        Merge report of MultiTest parts into test runner report.
        Return True if all parts are found and can be successfully merged.

        Format of test_report_lookup:
        {
            'report_uid_1': [
                (True, report_1_part_1), (True, report_1_part_2), ...
            ],
            'report_uid_2': [
                (True, report_2_part_1), (False, report_2_part_2), ...
            ],
            ...
        }
        """
        merge_result = True

        for uid, result in test_report_lookup.items():
            placeholder_report = self._result.test_report.get_by_uid(uid)
            num_of_parts = 0
            part_indexes = set()
            merged = False

            with placeholder_report.logged_exceptions():
                for run, report in result:
                    if num_of_parts and num_of_parts != report.part[1]:
                        raise ValueError(
                            "Cannot merge parts for child report with"
                            " `uid`: {uid}, invalid parameter of part"
                            " provided.".format(uid=uid)
                        )
                    elif report.part[0] in part_indexes:
                        raise ValueError(
                            "Cannot merge parts for child report with"
                            " `uid`: {uid}, duplicate MultiTest parts"
                            " had been scheduled.".format(uid=uid)
                        )
                    else:
                        part_indexes.add(report.part[0])
                        num_of_parts = report.part[1]

                    if run:
                        if isinstance(run, Exception):
                            raise run
                        else:
                            placeholder_report.merge(report, strict=False)
                    else:
                        raise MergeError(
                            "Cannot merge parts for child report with"
                            " `uid`: {uid}, at least one part (index:{part})"
                            " didn't run.".format(uid=uid, part=report.part[0])
                        )
                else:
                    if len(part_indexes) < num_of_parts:
                        raise MergeError(
                            "Cannot merge parts for child report with"
                            " `uid`: {uid}, not all MultiTest parts"
                            " had been scheduled.".format(uid=uid)
                        )
                merged = True

            # If fail to merge sibling reports, clear the placeholder report
            # but keep error logs, sibling reports will be appended at the end.
            if not merged:
                placeholder_report.entries = []
                placeholder_report._index = {}
                placeholder_report.status_override = Status.ERROR
                for _, report in result:
                    report.name = TEST_PART_PATTERN_FORMAT_STRING.format(
                        report.name, report.part[0], report.part[1]
                    )
                    report.uid = strings.uuid4()  # considered as error report
                    self._result.test_report.append(report)

            merge_result = (
                merge_result and placeholder_report.status != Status.ERROR
            )

        return merge_result

    def uid(self):
        """Entity uid."""
        return self.cfg.name

    def _log_test_status(self):
        if not self._result.test_report.entries:
            self.logger.warning(
                "No tests were run - check your filter patterns."
            )
        else:
            self.logger.log_test_status(
                self.cfg.name, self._result.test_report.status
            )

    def _pre_exporters(self):
        # Apply report filter if one exists
        if self.cfg.reporting_filter is not None:
            self._result.test_report = self.cfg.reporting_filter(
                self._result.test_report
            )

    def _invoke_exporters(self) -> None:
        # Add this logic into a ReportExporter(Runnable)
        # that will return a result containing errors

        if hasattr(self._result.test_report, "bubble_up_attachments"):
            self._result.test_report.bubble_up_attachments()

        export_context = ExportContext()
        for exporter in self.exporters:
            if isinstance(exporter, test_exporters.Exporter):
                run_exporter(
                    exporter=exporter,
                    source=self._result.test_report,
                    export_context=export_context,
                )
            else:
                raise NotImplementedError(
                    "Exporter logic not implemented for: {}".format(
                        type(exporter)
                    )
                )

        self._result.exporter_results = export_context.results

    def _post_exporters(self):
        # View report in web browser if "--browse" specified
        report_urls = []
        report_opened = False

        for result in self._result.exporter_results:
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

    def abort_dependencies(self):
        """
        Yield all dependencies to be aborted before self abort.
        """
        if self._ihandler is not None:
            yield self._ihandler
        yield from super(TestRunner, self).abort_dependencies()

    def aborting(self):
        """Stop the web server if it is running."""
        if self._web_server_thread is not None:
            self._web_server_thread.stop()
        self._close_file_logger()

    def _configure_stdout_logger(self):
        """Configure the stdout logger by setting the required level."""
        logger.STDOUT_HANDLER.setLevel(self.cfg.logger_level)

    def _configure_file_logger(self):
        """
        Configure the file logger to the specified log levels. A log file
        will be created under the runpath (so runpath must be created before
        this method is called).
        """
        if self.runpath is None:
            raise RuntimeError(
                "Need to set up runpath before configuring logger"
            )

        if self.cfg.file_log_level is None:
            self.logger.debug("Not enabling file logging")
        else:
            self._file_log_handler = logger.configure_file_logger(
                self.cfg.file_log_level, self.runpath
            )

    def _close_file_logger(self):
        """
        Closes the file logger, releasing all file handles. This is necessary to
        avoid permissions errors on Windows.
        """
        if self._file_log_handler is not None:
            self._file_log_handler.flush()
            self._file_log_handler.close()
            logger.TESTPLAN_LOGGER.removeHandler(self._file_log_handler)
            self._file_log_handler = None

    def run(self):
        """
        Executes the defined steps and populates the result object.
        """
        if self.cfg.test_lister:
            self._result.run = True
            return self._result

        return super(TestRunner, self).run()
