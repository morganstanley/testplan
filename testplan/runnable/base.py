"""Tests runner module."""

import os
import random
import time
import uuid
import webbrowser
from collections import OrderedDict

from schema import Or, And, Use

from testplan import defaults
from testplan.common.utils import logger
from testplan.common.config import ConfigOption
from testplan.common.entity import (Entity, RunnableConfig, RunnableStatus,
    RunnableResult, Runnable)
from testplan.common.exporters import BaseExporter, ExporterResult
from testplan.common.report import MergeError
from testplan.common.utils.path import default_runpath
from testplan.exporters import testing as test_exporters
from testplan.report.testing import TestReport, TestGroupReport, Status
from testplan.report.testing.styles import Style
from testplan.runnable.interactive import TestRunnerIHandler
from testplan.runners.base import Executor
from testplan.runners.pools.tasks import Task, TaskResult
from testplan.testing import listing, filtering, ordering, tagging
from testplan.testing.base import TestResult


def get_default_exporters(config):
    """
    Instantiate certain exporters if related cmdline argument (e.g. --pdf)
    is passed but there aren't any exporter declarations.
    """
    result = []
    if config.pdf_path:
        result.append(test_exporters.PDFExporter())
    if config.report_tags or config.report_tags_all:
        result.append(test_exporters.TagFilteredPDFExporter())
    if config.json_path:
        result.append(test_exporters.JSONExporter())
    if config.xml_dir:
        result.append(test_exporters.XMLExporter())
    if config.ui_port is not None:
        result.append(test_exporters.WebServerExporter(ui_port=config.ui_port))
    return result


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
        raise TypeError('Invalid exporter value: {}'.format(value))

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
    result.report = TestGroupReport(name=original_result.task.name)
    attrs = [attr for attr in original_result.task.all_attrs]
    result_lines = ['{}: {}'.format(attr, getattr(original_result.task, attr))\
                        if getattr(original_result.task, attr, None) else ''\
                    for attr in attrs]
    result.report.logger.error(
        os.linesep.join([line for line in result_lines if line]))
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
            'name': str,
            ConfigOption('description', default=None): Or(str, None),
            ConfigOption('logger_level', default=logger.TEST_INFO): int,
            ConfigOption('file_log_level', default=logger.DEBUG): Or(int, None),
            ConfigOption(
                'runpath',
                default=default_runpath,
                ): Or(None, str, lambda x: callable(x)),
            ConfigOption('path_cleanup', default=True): bool,
            ConfigOption('all_tasks_local', default=False): bool,
            ConfigOption('shuffle', default=[]): list,  # list of string choices
            ConfigOption(
                'shuffle_seed', default=float(random.randint(1, 9999))): float,
            ConfigOption(
                'exporters', default=None): Use(get_exporters),
            ConfigOption(
                'stdout_style', default=defaults.STDOUT_STYLE,): Style,
            ConfigOption(
                'report_dir', default=defaults.REPORT_DIR,): str,
            ConfigOption('xml_dir', default=None,): Or(str, None),
            ConfigOption('pdf_path', default=None,): Or(str, None),
            ConfigOption('json_path', default=None,): Or(str, None),
            ConfigOption('pdf_style', default=defaults.PDF_STYLE,): Style,
            ConfigOption('report_tags', default=[]
                         ): [Use(tagging.validate_tag_value)],
            ConfigOption('report_tags_all', default=[]
                         ): [Use(tagging.validate_tag_value)],
            ConfigOption('merge_scheduled_parts', default=False): bool,
            ConfigOption('browse', default=None): Or(None, bool),
            ConfigOption('ui_port', default=None): Or(None, int),
            ConfigOption('web_server_startup_timeout',
                         default=defaults.WEB_SERVER_TIMEOUT): int,
            ConfigOption('test_filter', default=filtering.Filter()
                        ): filtering.BaseFilter,
            ConfigOption('test_sorter', default=ordering.NoopSorter()
                         ): ordering.BaseSorter,
            # Test lister is None by default, otherwise Testplan would
            # list tests, not run them
            ConfigOption('test_lister', default=None
                         ):Or(None, listing.BaseLister),
            ConfigOption('verbose', default=False): bool,
            ConfigOption('debug', default=False): bool,
            ConfigOption(
                'timeout', default=None): Or(
                None, And(Or(int, float), lambda t: t >= 0)),
            ConfigOption('interactive_handler', default=TestRunnerIHandler):
                object,
            ConfigOption('extra_deps', default=[]): list
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
        super(TestRunnerResult, self). __init__()
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
        return self.test_report.passed and all(
            [exporter_result.success
             for exporter_result in self.exporter_results])


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
    :type timeout: ``NoneType`` or ``int`` or ``float`` greater than 0.
    :param interactive_handler: Handler for interactive mode execution.
    :type interactive_handler: Subclass of :py:class:
        `TestRunnerIHandler <testplan.runnable.interactive.TestRunnerIHandler>`
    :param extra_deps: Extra module dependencies for interactive reload.
    :type extra_deps: ``list`` of ``module``

    Also inherits all
    :py:class:`~testplan.common.entity.base.Runnable` options.
    """

    CONFIG = TestRunnerConfig
    STATUS = TestRunnerStatus
    RESULT = TestRunnerResult

    def __init__(self, **options):
        super(TestRunner, self).__init__(**options)
        self._start_time = time.time()
        self._tests = OrderedDict()  # uid to resource
        self._result.test_report = TestReport(
            name=self.cfg.name, uid=self.cfg.name)
        self._configure_stdout_logger()
        self._web_server_thread = None
        self._file_log_handler = None

    @property
    def report(self):
        """Tests report."""
        return self._result.test_report

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
        resource = self.resources[resource]\
            if resource else self.resources.environments
        target = env.create(parent=self)
        env_uid = env.uid()
        resource.add(target, env_uid)
        return env_uid

    def add_resource(self, resource, uid=None):
        """
        Adds a test
        :py:class:`executor <testplan.runners.base.Executor>`
        resource in the test runner environment.

        :param resource: Test executor to be added.
        :type resource: Subclass of :py:class:`~testplan.runners.base.Executor`
        :param uid: Optional input resource uid.
        :type uid: ``str``
        :return: Resource uid assigned.
        :rtype:  ``str``
        """
        resource.cfg.parent = self.cfg
        resource.parent = self
        return self.resources.add(
            resource, uid=uid or getattr(resource, 'uid', uuid.uuid4)())

    def schedule(self, task=None, resource=None, uid=None, **options):
        """
        Schedules a serializable
        :py:class:`~testplan.runners.pools.tasks.base.Task` in a task runner
        :py:class:`~testplan.runners.pools.base.Pool` executor resource.

        :param task: Input task.
        :param task: :py:class:`~testplan.runners.pools.tasks.base.Task`
        :param resource: Target pool resource.
        :param resource: :py:class:`~testplan.runners.pools.base.Pool`
        :param uid: Optional uid for task.
        :param uid: ``str``
        :param options: Task input options.
        :param options: ``dict``
        :return uid: Assigned uid for task.
        :rtype: ``str``
        """
        return self.add(task or Task(uid=uid, **options),
                        resource=resource, uid=uid)

    def add(self, runnable, resource=None, uid=None):
        """
        Adds a
        :py:class:`runnable <testplan.common.entity.base.Runnable>`
        tests entity to a :py:class:`~testplan.runners.base.Executor`
        resource.

        :param runnable: Test runner entity.
        :type runnable: :py:class:`~testplan.common.entity.base.Runnable`
        :param resource: Test executor resource.
        :type resource: :py:class:`~testplan.runners.base.Executor`
        :param uid: Optional test uid.
        :type uid: ``str``
        :return: Assigned uid for test.
        :rtype: ``str``
        """
        uid = uid or getattr(runnable, 'uid', uuid.uuid4)()
        if uid in self._tests:
            self.logger.error(
                'Skip adding {} with uid {}.. already added.'.format(
                    runnable, uid))
            return uid

        if isinstance(runnable, Entity):
            runnable.cfg.parent = self.cfg
            runnable.parent = self
        elif isinstance(runnable, Task):
            pass
        elif callable(runnable):
            runnable.parent_cfg = self.cfg
            runnable.parent = self

        # Check if test should not be added only when a filter is used.
        if type(self.cfg.test_filter) is not filtering.Filter or\
                    self.cfg.test_lister is not None:
            if not self.should_be_added(runnable):
                return None

        if resource is None:
            resource = self.resources.first()  # Implies local_runner
        if resource not in self.resources:
            raise RuntimeError(
                'Resource "{}" does not exist.'.format(resource))
        if self.cfg.interactive and isinstance(runnable, Task):
            runnable = runnable.materialize()
            self.resources[resource].add(runnable, runnable.uid() or uid)
        else:
            self.resources[resource].add(runnable, uid)
        self._tests[uid] = resource
        return uid

    def should_be_added(self, runnable):
        """Determines if a test runnable should be added for execution."""
        if isinstance(runnable, Task):
            target = runnable.materialize()
            target.cfg.parent = self.cfg
            target.parent = self

        elif callable(runnable):
            target = runnable()
            target.cfg.parent = runnable.parent_cfg
            target.parent = runnable.parent
        else:
            target = runnable

        should_run = target.should_run()
        self.logger.debug('should_run %s? %s', target.name, bool(should_run))

        # --list always returns False
        if should_run and self.cfg.test_lister is not None:
            self.cfg.test_lister.log_test_info(target)
            return False

        return should_run

    def _add_step(self, step, *args, **kwargs):
        if self.cfg.test_lister is None:
            super(TestRunner, self)._add_step(step, *args, **kwargs)

    def _record_start(self):
        self.report.timer.start('run')

    def _record_end(self):
        self.report.timer.end('run')

    def make_runpath_dirs(self):
        super(TestRunner, self).make_runpath_dirs()
        self.logger.info('{} runpath: {}'.format(self, self.runpath))

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
                    'Aborting {} due to start exception:'.format(resource))
                self.logger.error(exception)
                resource.abort()

        while self.active:
            if self.cfg.timeout and \
                    time.time() - self._start_time > self.cfg.timeout:
                self.result.test_report.logger.error(
                    'Timeout: Aborting execution after {} seconds'.format(
                        self.cfg.timeout))
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
                        'Aborting {} - {} unexpectedly died'.format(
                            self, resource))
                    self.abort()
                    self.result.test_report.status_override = Status.ERROR

            if pending_work is False:
                break
            time.sleep(self.cfg.active_loop_sleep)

    def _create_result(self):
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

            report = test_results[uid].report
            if report.part and self.cfg.merge_scheduled_parts:
                # Save the report temporarily and later will merge it
                test_rep_lookup.setdefault(report.uid, []).append(
                    (test_results[uid].run, report))
                try:
                    test_report.get_by_uid(report.uid)
                    continue
                except KeyError:
                    # A report will be created and then append as a placeholder
                    if isinstance(resource_result, TaskResult):
                        # 'target' should be an instance of MultiTest since the
                        # corresponding report has 'part' defined. We can get
                        # a full structured report by dry_run(), thus the order
                        # of testcases can be retained in test report.
                        target = resource_result.task.materialize()
                        # TODO: Any idea to avoid accessing private members?
                        target.cfg._options['part'] = None
                        target._test_context = None
                        report = target.dry_run(status=Status.SKIPPED).report
                    else:
                        report = report.__class__(report.name,
                                                  category=report.category,
                                                  uid=report.uid)
            elif report.part:
                report.name = '{} - part({}/{})'.format(
                    report.name, report.part[0] + 1, report.part[1])
                # Change report uid to avoid conflict during appending
                report.uid = uuid.uuid4()

            test_report.append(report)
            step_result = step_result and test_results[uid].run

        if test_rep_lookup:
            step_result = self._merge_reports(test_rep_lookup) and step_result

        # The uids of a test report and all of its children
        # should be comply with standard UUID form
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

        for uid, reports in test_report_lookup.items():
            count = reports[0][1].part[1]  # How many parts scheduled
            placeholder_report = self._result.test_report.get_by_uid(uid)
            reports.sort(key=lambda tup: tup[1].part[0])

            with placeholder_report.logged_exceptions():
                if len(reports) < count:
                    raise MergeError(
                        'Cannot merge parts for child report with '
                        '`uid`: {uid}, not all MultiTest parts '
                        'had been scheduled.'.format(uid=uid))

                if any(sibling_report.part[0] != idx or
                       sibling_report.part[1] != count
                       for idx, (run, sibling_report) in enumerate(reports)):
                        raise ValueError(
                            'Cannot merge parts for child report with '
                            '`uid`: {uid}, invalid parameter of part '
                            'provided.'.format(uid=uid))

            with placeholder_report.logged_exceptions():
                for run, sibling_report in reports:
                    if run and not isinstance(run, Exception):
                        placeholder_report.merge(sibling_report, strict=False)
                    else:
                        placeholder_report.status_override = Status.ERROR

            merge_result = merge_result and \
                           placeholder_report.status != Status.ERROR

        return merge_result

    def uid(self):
        """Entity uid."""
        return self.cfg.name

    def _log_test_status(self):
        if not self._result.test_report.entries:
            self.logger.warning(
                'No tests were run - check your filter patterns.')
            self._result.test_report.status_override = Status.FAILED
        else:
            self.logger.log_test_status(self.cfg.name,
                                        self._result.test_report.passed)

    def _invoke_exporters(self):
        # Add this logic into a ReportExporter(Runnable)
        # that will return a result containing errors
        if self.cfg.exporters is None or len(self.cfg.exporters) == 0:
            exporters = get_default_exporters(self.cfg)
        else:
            exporters = self.cfg.exporters

        if hasattr(self._result.test_report, 'bubble_up_attachments'):
            self._result.test_report.bubble_up_attachments()

        for exporter in exporters:

            if hasattr(exporter, 'cfg'):
                exporter.cfg.parent = self.cfg

            if isinstance(exporter, test_exporters.Exporter):
                exp_result = ExporterResult.run_exporter(
                    exporter=exporter,
                    source=self._result.test_report,
                    type='test',
                )

                if not exp_result.success:
                    logger.TESTPLAN_LOGGER.error(exp_result.traceback)
                self._result.exporter_results.append(exp_result)
            else:
                raise NotImplementedError(
                    'Exporter logic not'
                    ' implemented for: {}'.format(type(exporter)))

    def _post_exporters(self):
        report_opened = False
        for result in self._result.exporter_results:
            if getattr(result.exporter, 'url', None) and self.cfg.browse:
                webbrowser.open(result.exporter.url)
                report_opened = True
            if getattr(result.exporter, '_web_server_thread', None):
                # Wait for web server to terminate.
                self._web_server_thread = result.exporter._web_server_thread
                self._web_server_thread.join()

        if self.cfg.browse and not report_opened:
            self.logger.warning(('No reports opened, could not find an '
                                 'exported result to browse'))

    def aborting(self):
        """Stop the web server if it is running."""
        if self._web_server_thread is not None:
            self._web_server_thread.stop()

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
                'Need to set up runpath before configuring logger')

        if self.cfg.file_log_level is None:
            self.logger.debug('Not enabling file logging')
        else:
            self._file_log_handler = logger.configure_file_logger(
                self.cfg.file_log_level, self.runpath)

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
