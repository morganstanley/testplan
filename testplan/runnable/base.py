"""Tests runner module."""

import os
import random
import time
import datetime
import webbrowser
from collections import OrderedDict

import pytz
from schema import Or, And, Use

from testplan import defaults
from testplan.common.config import ConfigOption
from testplan.common.entity import (
    RunnableConfig,
    RunnableStatus,
    RunnableResult,
    Runnable,
)
from testplan.common.exporters import BaseExporter, ExporterResult
from testplan.common.report import MergeError
from testplan.common.utils import logger
from testplan.common.utils import strings
from testplan.common.utils.path import default_runpath
from testplan.exporters import testing as test_exporters
from testplan.report import (
    TestReport,
    TestGroupReport,
    Status,
    ReportCategories,
)
from testplan.report.testing.styles import Style
from testplan.runnable.interactive import TestRunnerIHandler
from testplan.runners.base import Executor
from testplan.runners.pools.tasks import Task, TaskResult
from testplan.testing import listing, filtering, ordering, tagging
from testplan.testing.base import TestResult


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
        name=original_result.task.name, category=ReportCategories.ERROR
    )
    attrs = [attr for attr in original_result.task.all_attrs]
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
            ConfigOption("logger_level", default=logger.TEST_INFO): int,
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
                None, listing.BaseLister
            ),
            ConfigOption("verbose", default=False): bool,
            ConfigOption("debug", default=False): bool,
            ConfigOption("timeout", default=defaults.TESTPLAN_TIMEOUT): Or(
                None, And(int, lambda t: t >= 0)
            ),
            ConfigOption("abort_wait_timeout", default=60): int,
            ConfigOption(
                "interactive_handler", default=TestRunnerIHandler
            ): object,
            ConfigOption("extra_deps", default=[]): list,
            ConfigOption("label", default=None): Or(None, str),
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

    Also inherits all
    :py:class:`~testplan.common.entity.base.Runnable` options.
    """

    CONFIG = TestRunnerConfig
    STATUS = TestRunnerStatus
    RESULT = TestRunnerResult

    def __init__(self, **options):
        super(TestRunner, self).__init__(**options)
        self._tests = OrderedDict()  # uid to resource, in definition order

        self._part_instance_names = set()  # name of Multitest part
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
        self._reset_report_uid = self.cfg.interactive_port is None

    @property
    def report(self):
        """Tests report."""
        return self._result.test_report

    @property
    def exporters(self):
        """
        Return a list of
        :py:class:`Resources <testplan.exporters.testing.base.Exporter>`.
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
        return exporters

    def add_environment(self, env, resource=None):
        """
        Adds an environment to the target resource holder.

        :param env: Environment creator instance.
        :type env: Subclass of
          :py:class:`~testplan.environment.EnvironmentCreator`
        :param resource: Target environments holder resource.
        :param resource: Subclass of
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

    def add_resource(self, resource, uid=None):
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
        resource.parent = self
        resource.cfg.parent = self.cfg
        return self.resources.add(
            resource, uid=uid or getattr(resource, "uid", strings.uuid4)()
        )

    def schedule(self, task=None, resource=None, **options):
        """
        Schedules a serializable
        :py:class:`~testplan.runners.pools.tasks.base.Task` in a task runner
        :py:class:`~testplan.runners.pools.base.Pool` executor resource.

        :param task: Input task.
        :param task: :py:class:`~testplan.runners.pools.tasks.base.Task`
        :param resource: Target pool resource.
        :param resource: :py:class:`~testplan.runners.pools.base.Pool`
        :param options: Task input options.
        :param options: ``dict``
        :return uid: Assigned uid for task.
        :rtype: ``str``
        """
        return self.add(task or Task(**options), resource=resource)

    def add(self, target, resource=None):
        """
        Adds a :py:class:`runnable <testplan.common.entity.base.Runnable>`
        test entity, or a :py:class:`~testplan.runners.pools.tasks.base.Task`,
        or a callable that returns a test entity to a
        :py:class:`~testplan.runners.base.Executor` resource.

        :param target: Test target.
        :type target: :py:class:`~testplan.common.entity.base.Runnable` or
            :py:class:`~testplan.runners.pools.tasks.base.Task` or ``callable``
        :param resource: Test executor resource.
        :type resource: :py:class:`~testplan.runners.base.Executor`
        :return: Assigned uid for test.
        :rtype: ``str`` or ```NoneType``
        """
        local_runner = self.resources.first()
        resource = resource or local_runner

        if resource not in self.resources:
            raise RuntimeError(
                'Resource "{}" does not exist.'.format(resource)
            )

        # Get the real test entity and verify if it should be added
        runnable = self._verify_test_target(target)
        if not runnable:
            return None

        uid = runnable.uid()
        part = getattr(getattr(runnable, "cfg", {"part": None}), "part", None)

        # Uid of test entity MUST be unique, generally the uid of a test entity
        # is the same as its name. When a test entity is split into multi-parts
        # the uid will change (e.g. with a postfix), however its name should be
        # different from uids of all non-part entities, and its uid cannot be
        # the same as the name of any test entity.
        if uid in self._tests:
            raise ValueError(
                '{} with uid "{}" already added.'.format(self._tests[uid], uid)
            )
        if uid in self._part_instance_names:
            raise ValueError(
                'Multitest part named "{}" already added.'.format(uid)
            )
        if part:
            if runnable.name in self._tests:
                raise ValueError(
                    '{} with uid "{}" already added.'.format(
                        self._tests[runnable.name], runnable.name
                    )
                )
            self._part_instance_names.add(runnable.name)

        # When running interactively, add all real test entities into the local
        # runner even if they were scheduled into a pool. It greatly simplifies
        # the interactive runner if it only has to deal with the local runner.
        if self.cfg.interactive_port is not None:
            self._tests[uid] = local_runner
            self.resources[local_runner].add(runnable, uid)
            return uid

        # Reset the task uid which will be used for test result transport in
        # a pool executor, it makes logging or debugging easier.
        if isinstance(target, Task):
            target._uid = uid

        # In batch mode the original target is added into executors, it can be:
        # 1> A runnable object (generally a test entity or customized by user)
        # 2> A callable that returns a runnable object
        # 3> A task that wrapped a runnable object
        self._tests[uid] = resource
        self.resources[resource].add(target, uid)
        return uid

    def _verify_test_target(self, target):
        """
        Determines if a test target should be added for execution.
        Returns the real test entity if it should run, otherwise None.
        """
        # The target added into TestRunner can be: 1> a real test entity
        # 2> a task wraps a test entity 3> a callable returns a test entity
        if isinstance(target, Runnable):
            runnable = target
        elif isinstance(target, Task):
            runnable = target.materialize()
        elif callable(target):
            runnable = target()
        else:
            raise TypeError(
                "Unrecognized test target of type {}".format(type(target))
            )

        if isinstance(runnable, Runnable):
            runnable.parent = self
            runnable.cfg.parent = self.cfg

        if type(self.cfg.test_filter) is not filtering.Filter:
            should_run = runnable.should_run()
            self.logger.debug(
                "Should run %s? %s",
                runnable.name,
                "Yes" if should_run else "No",
            )
            if not should_run:
                return None

        # "--list" option means always not executing tests
        if self.cfg.test_lister is not None:
            self.cfg.test_lister.log_test_info(runnable)
            return None

        return runnable

    def _add_step(self, step, *args, **kwargs):
        if self.cfg.test_lister is None:
            super(TestRunner, self)._add_step(step, *args, **kwargs)

    def _record_start(self):
        self.report.timer.start("run")

    def _record_end(self):
        self.report.timer.end("run")

    def make_runpath_dirs(self):
        super(TestRunner, self).make_runpath_dirs()
        self.logger.test_info("Testplan runpath: {}".format(self.runpath))

    def pre_resource_steps(self):
        """Steps to be executed before resources started."""
        # self._add_step(self._runpath_initialization)
        self._add_step(self._record_start)
        self._add_step(self.make_runpath_dirs)
        self._add_step(self._configure_file_logger)

    def main_batch_steps(self):
        """Steps to be executed while resources are running."""
        self._add_step(self._wait_ongoing)

    def post_resource_steps(self):
        """Steps to be executed after resources stopped."""
        self._add_step(self._create_result)
        self._add_step(self._log_test_status)
        self._add_step(self._record_end)  # needs to happen before export
        self._add_step(self._invoke_exporters)
        self._add_step(self._post_exporters)
        self._add_step(self._close_file_logger)

    def _wait_ongoing(self):
        # TODO: if a pool fails to initialize we could reschedule the tasks.
        if self.resources.start_exceptions:
            for resource, exception in self.resources.start_exceptions.items():
                self.logger.critical(
                    "Aborting {} due to start exception:".format(resource)
                )
                self.logger.error(exception)
                resource.abort()

        _start_ts = (
            self.result.test_report.timer["run"][0]
            - datetime.datetime(1970, 1, 1, tzinfo=pytz.utc)
        ).total_seconds()

        while self.active:
            if self.cfg.timeout and time.time() - _start_ts > self.cfg.timeout:
                self.result.test_report.logger.error(
                    "Timeout: Aborting execution after {} seconds".format(
                        self.cfg.timeout
                    )
                )
                # Abort dependencies, wait sometime till test reports are ready
                for dep in self.abort_dependencies():
                    self._abort_entity(dep)
                time.sleep(self.cfg.abort_wait_timeout)
                break

            pending_work = False
            for resource in self.resources:
                # Check if any resource has pending work.
                # Maybe print periodically the pending work of resource.
                pending_work = resource.pending_work() or pending_work

                # Poll the resource's health - if it has unexpectedly died
                # then abort the entire test to avoid hanging.
                if not resource.is_alive:
                    self.result.test_report.logger.critical(
                        "Aborting {} - {} unexpectedly died".format(
                            self, resource
                        )
                    )
                    self.abort()
                    self.result.test_report.status_override = Status.ERROR

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
                    report.category != "task_rerun"
                    and self.cfg.merge_scheduled_parts
                ):
                    report.uid = report.name
                    # Save the report temporarily and later will merge it
                    test_rep_lookup.setdefault(report.uid, []).append(
                        (test_results[uid].run, report)
                    )
                    if report.uid not in test_report.entry_uids:
                        # Create a placeholder for merging sibling reports
                        if isinstance(resource_result, TaskResult):
                            # `runnable` must be an instance of MultiTest since
                            # the corresponding report has `part` defined. Can
                            # get a full structured report by `dry_run` and the
                            # order of testsuites/testcases can be retained.
                            runnable = resource_result.task.materialize()
                            runnable.parent = self
                            runnable.cfg.parent = self.cfg
                            runnable.cfg._options["part"] = None
                            runnable._test_context = None
                            report = runnable.dry_run().report

                        else:
                            report = report.__class__(
                                report.name,
                                uid=report.uid,
                                category=report.category,
                            )
                    else:
                        continue  # Wait all sibling reports collected
                else:
                    # If do not want to merge sibling reports, then display
                    # them with different names. (e.g. `MTest - part(0/3)`)
                    report.name = report.uid

            test_report.append(report)
            step_result = step_result and run is True  # boolean or exception

        step_result = self._merge_reports(test_rep_lookup) and step_result

        # Reset UIDs of the test report and all of its children in UUID4 format
        if self._reset_report_uid:
            test_report.reset_uid()

        return step_result

    def _merge_reports(self, test_report_lookup):
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
                    report.name = "{} - part({}/{})".format(
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
            self._result.test_report.status_override = Status.FAILED
        else:
            self.logger.log_test_status(
                self.cfg.name, self._result.test_report.status
            )

    def _invoke_exporters(self):
        # Add this logic into a ReportExporter(Runnable)
        # that will return a result containing errors

        if hasattr(self._result.test_report, "bubble_up_attachments"):
            self._result.test_report.bubble_up_attachments()

        for exporter in self.exporters:
            if isinstance(exporter, test_exporters.Exporter):
                exp_result = ExporterResult.run_exporter(
                    exporter=exporter,
                    source=self._result.test_report,
                    type="test",
                )

                if not exp_result.success:
                    logger.TESTPLAN_LOGGER.error(exp_result.traceback)
                self._result.exporter_results.append(exp_result)
            else:
                raise NotImplementedError(
                    "Exporter logic not implemented for: {}".format(
                        type(exporter)
                    )
                )

    def _post_exporters(self):
        # View report in web browser if "--browse" specified
        report_urls = []
        report_opened = False

        for result in self._result.exporter_results:
            exporter = result.exporter
            if getattr(exporter, "report_url", None) and self.cfg.browse:
                report_urls.append(exporter.report_url)
            if getattr(exporter, "_web_server_thread", None):
                # Give priority to open report from local server
                webbrowser.open(exporter.report_url)
                report_opened = True
                # Stuck here waiting for web server to terminate
                self._web_server_thread = exporter._web_server_thread
                self._web_server_thread.join()

        if self.cfg.browse and not report_opened:
            if len(report_urls) > 0:
                for report_url in report_urls:
                    webbrowser.open(report_url)
            else:
                self.logger.warning(
                    "No reports opened, could not find "
                    "an exported result to browse"
                )

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
