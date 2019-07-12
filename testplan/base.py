"""Testplan base module."""

import random

from testplan.runnable import TestRunnerConfig, TestRunnerResult, TestRunner
from .common.config import ConfigOption
from .common.entity import (RunnableManager, RunnableManagerConfig, Resource)
from .common.utils.callable import arity
from .common.utils.validation import is_subclass, has_method
from .parser import TestplanParser
from .runners import LocalRunner
from .environment import Environments
from testplan.common.utils import logger
from testplan.common.utils import path
from testplan import defaults
from testplan.testing import filtering
from testplan.testing import ordering


class TestplanConfig(RunnableManagerConfig, TestRunnerConfig):
    """
    Configuration object for
    :py:class:`~testplan.base.Testplan` entity.
    """

    @classmethod
    def get_options(cls):
        """Additional config options for Testplan class"""
        return {
            ConfigOption(
                'runnable', default=TestRunner): is_subclass(TestRunner),
            ConfigOption('resources', default=[]): [Resource],
            ConfigOption(
                'parser', default=TestplanParser): has_method('parse_args')
        }


class TestplanResult(TestRunnerResult):
    """
    Result object of a :py:class:`~testplan.base.Testplan`
    :py:class:`runnable manager <testplan.common.entity.base.RunnableManager>`
    entity.
    """

    def __init__(self):
        super(TestplanResult, self). __init__()
        self.decorated_value = None

    @property
    def exit_code(self):
        """System exit code based on successful run."""
        return 0 if getattr(self, 'run', False) and self.success else 1

    def __bool__(self):
        """
        To be used by ``sys.exit(not main())`` pattern.
        """
        return True if self.exit_code == 0 else False
    __nonzero__ = __bool__


class Testplan(RunnableManager):
    """
    A collection of tests and tests executors with the ability to
    selectively execute a subset or a shuffled set of those tests.

    It manages a
    :py:class:`~testplan.runnable.TestRunner` to execute the tests
    and also accepts all :py:class:`~testplan.runnable.TestRunnerConfig`
    options.

    Since it's a manager of a TestRunner object, it **exposes all**
    :py:class:`~testplan.runnable.TestRunner`,
    attributes and methods like
    :py:meth:`~testplan.runnable.TestRunner.add_resource`,
    :py:meth:`~testplan.runnable.TestRunner.add`, and
    :py:meth:`~testplan.runnable.TestRunner.schedule`.

    :param runnable: Test runner.
    :type runnable: :py:class:`~testplan.runnable.TestRunner`
    :param resources: Initial resources. By default, one LocalRunner is added to
      execute the Tests.
    :type resources:
      ``list`` of :py:class:`resources <testplan.common.entity.base.Resource>`
    :param parser: Command line parser.
    :type parser: :py:class:`~testplan.parser.TestplanParser`

    Also inherits all
    :py:class:`~testplan.common.entity.base.RunnableManager` and
    :py:class:`~testplan.runnable.TestRunner` options.
    """

    CONFIG = TestplanConfig

    def __init__(self,
                 name,
                 logger_level=logger.TEST_INFO,
                 file_log_level=logger.DEBUG,
                 runpath=path.default_runpath,
                 path_cleanup=True,
                 all_tasks_local=False,
                 shuffle=None,
                 shuffle_seed=float(random.randint(1, 9999)),
                 exporters=None,
                 stdout_style=defaults.STDOUT_STYLE,
                 report_dir=defaults.REPORT_DIR,
                 xml_dir=None,
                 pdf_path=None,
                 json_path=None,
                 pdf_style=defaults.PDF_STYLE,
                 report_tags=None,
                 report_tags_all=None,
                 merge_schedule_parts=False,
                 browse=None,
                 ui_port=None,
                 web_server_startup_timeout=defaults.WEB_SERVER_TIMEOUT,
                 test_filter=filtering.Filter(),
                 test_sorter=ordering.NoopSorter(),
                 test_lister=None,
                 verbose=False,
                 debug=False,
                 timeout=None,
                 extra_deps=None,
                 interactive=False,
                 **options):

        # TODO add a utility to reduce this boilerplate.
        if shuffle is None:
            shuffle = []
        if extra_deps is None:
            extra_deps = []
        if report_tags is None:
            report_tags = []
        if report_tags_all is None:
            report_tags_all = []

        super(Testplan, self).__init__(
            name=name,
            logger_level=logger_level,
            file_log_level=file_log_level,
            runpath=runpath,
            path_cleanup=path_cleanup,
            all_tasks_local=all_tasks_local,
            shuffle=shuffle,
            shuffle_seed=shuffle_seed,
            exporters=exporters,
            stdout_style=stdout_style,
            report_dir=report_dir,
            xml_dir=xml_dir,
            pdf_path=pdf_path,
            json_path=json_path,
            pdf_style=pdf_style,
            report_tags=report_tags,
            report_tags_all=report_tags_all,
            merge_schedule_parts=merge_schedule_parts,
            browse=browse,
            ui_port=ui_port,
            web_server_startup_timeout=web_server_startup_timeout,
            test_filter=test_filter,
            test_sorter=test_sorter,
            test_lister=test_lister,
            verbose=verbose,
            debug=debug,
            timeout=timeout,
            extra_deps=extra_deps,
            interactive=interactive,
            **options)
        for resource in self._cfg.resources:
            self._runnable.add_resource(resource)

        # Stores local tests.
        self._runnable.add_resource(LocalRunner(), uid='local_runner')

        # Stores independent environments.
        self._runnable.add_resource(Environments(), uid='environments')

    @property
    def parser(self):
        """Returns a new command line parser."""
        return self._cfg.parser(name=self._cfg.name)

    @property
    def args(self):
        """Parsed arguments."""
        return self._parsed_args

    @property
    def processed_args(self):
        """Processed parsed arguments."""
        return self._processed_args

    def _enrich_options(self, options):
        """
        Enrich the options using parsed command line arguments.

        The command line arguments will not have any effect if we
        already have an explicit programmatic declaration for a given
        keyword.
        """
        parser = self._cfg.parser(name=self._cfg.name, default_options=options)
        self._parsed_args = parser.parse_args()
        self._processed_args = parser.process_args(self._parsed_args)
        return options

    def run(self):
        """
        TODO
        Runs the tests added and returns the result object.

        :return: Result containing tests and execution steps results.
        :rtype: :py:class:`~testplan.base.TestplanResult`
        """
        result = super(Testplan, self).run()
        if isinstance(result, TestRunnerResult):
            testplan_result = TestplanResult()
            testplan_result.__dict__ = result.__dict__
            return testplan_result
        return result

    @classmethod
    def main_wrapper(cls, **options):
        """
        Decorator that will be used for wrapping `main` methods in test scripts.

        It accepts all arguments of a
        :py:class:`~testplan.base.Testplan` entity.
        """
        def test_plan_inner(definition):
            """
            This is being passed the user-defined testplan entry point.
            """

            def test_plan_inner_inner():
                """
                This is the callable returned in the end, it executes the plan
                and the associated reporting
                """
                plan = cls(**options)
                try:
                    if arity(definition) == 2:
                        returned = definition(plan, plan.parser)
                    else:
                        returned = definition(plan)
                except Exception:
                    print('Exception in test_plan definition, aborting plan..')
                    plan.abort()
                    raise
                plan_result = plan.run()
                plan_result.decorated_value = returned
                return plan_result
            return test_plan_inner_inner
        return test_plan_inner


test_plan = Testplan.main_wrapper
