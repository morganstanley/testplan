"""Tests runner module."""

import os
import random
import time
import uuid
import webbrowser

from collections import OrderedDict

from schema import Schema, Or, Use

from testplan import defaults
from testplan.common.config import ConfigOption
from testplan.common.entity import Entity, RunnableConfig, RunnableStatus, \
    RunnableResult, Runnable
from testplan.common.exporters import BaseExporter, ExporterResult
from testplan.common.utils.path import default_runpath
from testplan.exporters import testing as test_exporters
from testplan.logger import log_test_status, TEST_INFO, TESTPLAN_LOGGER

from testplan.testing.base import TestResult

from testplan.report import TestReport
from testplan.report.testing import TestGroupReport, Status
from testplan.report.testing.styles import Style
from testplan.testing import listing, filtering, ordering, tagging

from .runners.base import Executor
from .runners.pools.tasks import Task, TaskResult


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
            ConfigOption('logger_level', default=TEST_INFO): int,
            ConfigOption(
                'runpath', default=default_runpath,
                block_propagation=False): Or(None, str, lambda x: callable(x)),
            ConfigOption('path_cleanup', default=True): bool,
            ConfigOption('all_tasks_local', default=False): bool,
            ConfigOption('shuffle', default=[]): list, # list of string choices
            ConfigOption(
                'shuffle_seed', default=float(random.randint(1, 9999))): float,
            ConfigOption(
                'exporters', default=None): Use(get_exporters),
            ConfigOption(
                'stdout_style', default=defaults.STDOUT_STYLE,
                block_propagation=False): Style,
            ConfigOption(
                'report_dir', default=defaults.REPORT_DIR,
                block_propagation=False): str,
            ConfigOption(
                'xml_dir', default=None,
                block_propagation=False): Or(str, None),
            ConfigOption(
                'pdf_path', default=None,
                block_propagation=False): Or(str, None),
            ConfigOption(
                'json_path', default=None,
                block_propagation=False): Or(str, None),
            ConfigOption(
                'pdf_style', default=defaults.PDF_STYLE,
                block_propagation=False): Style,
            ConfigOption('report_tags', default=[],
                block_propagation=False): [Use(tagging.validate_tag_value)],
            ConfigOption('report_tags_all', default=[],
                block_propagation=False): [Use(tagging.validate_tag_value)],
            ConfigOption('browse', default=False): bool,
            ConfigOption(
                'test_filter', default=filtering.Filter(),
                block_propagation=False): filtering.BaseFilter,
            ConfigOption(
                'test_sorter', default=ordering.NoopSorter(),
                block_propagation=False): ordering.BaseSorter,
            # Test lister is None by default, otherwise Testplan would
            # list tests, not run them
            ConfigOption('test_lister', default=None,
                block_propagation=False): Or(None, listing.BaseLister),
            ConfigOption('verbose', default=False,
                         block_propagation=False): bool,
            ConfigOption('debug', default=False,
                         block_propagation=False): bool
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
    """
    Adds tests to test
    :py:class:`executor <testplan.runners.base.Executor>` resources
    and invoke report
    :py:class:`exporter <testplan.exporters.testing.base.Exporter>` objects
    to create the
    :py:class:`~testplan.runnable.TestRunnerResult`.

    :param name: Name of test runner.
    :type name: ``str``
    :param logger_level: Logger level.
    :type logger_level: ``int``
    :param runpath: Input runpath.
    :type runpath: ``str`` or ``callable``
    :param path_cleanup: Clean previous runpath entries.
    :type path_cleanup: ``bool``
    :param all_tasks_local: TODO
    :type all_tasks_local: ``bool``
    :param shuffle: Shuffle strategy.
    :type shuffle: ``list`` of ``str``
    :param shuffle_seed: Shuffle seed.
    :type shuffle_seed: ``float``
    :param exporters: Exporters for reports creation.
    :type exporters: ``list``
    :param stdout_style: Styling output options.
    :type stdout_style: :py:class:`Style <testplan.report.testing.styles.Style>`
    :param report_dir: Report directory.
    :type report_dir: ``str``
    :param xml_dir: XML output directory.
    :type xml_dir: ``str``
    :param pdf_path: PDF output path ..path/*.pdf.
    :type pdf_path: ``str``
    :param json_path: JSON output path ..path/*.json.
    :type json_path: ``str``
    :param pdf_style: PDF creation styling options.
    :type pdf_style: :py:class:`Style <testplan.report.testing.styles.Style>`
    :param report_tags: Matches tests marked with any of the given tags.
    :type report_tags: ``list``
    :param report_tags_all: Match tests marked with all of the given tags.
    :type report_tags_all: ``list``
    :param test_filter: Tests filtering class.
    :type test_filter: Subclass of
      :py:class:`BaseFilter <testplan.testing.filtering.BaseFilter>`
    :param test_sorter: Tests sorting class.
    :type test_sorter: Subclass of
      :py:class:`BaseSorter <testplan.testing.ordering.BaseSorter>`
    :param test_lister: Tests listing class.
    :type test_lister: Subclass of
      :py:class:`BaseLister <testplan.testing.listing.BaseLister>`

    Also inherits all
    :py:class:`~testplan.common.entity.base.Runnable` options.
    """

    CONFIG = TestRunnerConfig
    STATUS = TestRunnerStatus
    RESULT = TestRunnerResult

    def __init__(self, **options):
        super(TestRunner, self).__init__(**options)
        self._tests = OrderedDict()  # uid to resource
        self._result.test_report = TestReport(name=self.cfg.name)

    @property
    def report(self):
        """Tests report."""
        return self._result.test_report

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
        :py:class:`runnable <testplan.common.entity.base.Runnable>` tests entity
        to an :py:class:`~testplan.runners.base.Executor` resource.

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
            resource = self.resources.first()
        if resource not in self.resources:
            raise RuntimeError('Resource "{}" does not exist.'.format(resource))
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

    def _wait_ongoing(self):
        # TODO: if a pool fails to initialize we could reschedule the tasks.
        if self.resources.start_exceptions:
            for resource, exception in self.resources.start_exceptions.items():
                self.logger.critical(
                    'Aborting {} due to start exception:'.format(resource))
                self.logger.error(exception)
                resource.abort()

        while self.active:
            ongoing = False
            for resource in self.resources:
                if resource.ongoing:
                    # Maybe print periodically ongoing resource
                    ongoing = True
            if ongoing is False:
                break
            time.sleep(self.cfg.active_loop_sleep)

    def _create_result(self):
        step_result = True
        test_results = self._result.test_results
        for uid, resource in self._tests.items():
            if not isinstance(self.resources[resource], Executor):
                continue
            resource_result = self.resources[resource].results[uid]
            if isinstance(resource_result, TaskResult):
                if resource_result.status is False:
                    test_results[uid] = result_for_failed_task(resource_result)
                else:
                    test_results[uid] = resource_result.result
            else:
                test_results[uid] = resource_result
            self._result.test_report.append(test_results[uid].report)
            step_result = step_result and test_results[uid].run
        return step_result

    def uid(self):
        """Entity uid."""
        return self.cfg.name

    def _log_test_status(self):
        log_test_status(
            name=self.cfg.name,
            passed=self._result.test_report.passed
        )

    def _invoke_exporters(self):
        # Add this logic into a ReportExporter(Runnable)
        # that will return a result containing errors
        if self.cfg.exporters is None:
            exporters = get_default_exporters(self.cfg)
        else:
            exporters = self.cfg.exporters

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
                    TESTPLAN_LOGGER.error(exp_result.traceback)
                self._result.exporter_results.append(exp_result)
            else:
                raise NotImplementedError(
                    'Exporter logic not'
                    ' implemented for: {}'.format(type(exporter)))

    def _post_exporters(self):
        if self.cfg.browse:
            # Open exporter url to browse.
            for result in self._result.exporter_results:
                if result.exporter.url is not None:
                    webbrowser.open(result.exporter.url)
                    break

    def aborting(self):
        """Suppressing not implemented debug log from parent class."""
        pass
