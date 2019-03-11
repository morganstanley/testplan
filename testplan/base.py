"""Testplan base module."""

from testplan.runnable import TestRunnerConfig, TestRunnerResult, TestRunner
from .common.config import ConfigOption
from .common.entity import (RunnableManager, RunnableManagerConfig, Resource)
from .common.utils.callable import arity
from .common.utils.validation import is_subclass, has_method
from .parser import TestplanParser
from .runners import LocalRunner
from .environment import Environments


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

    def __init__(self, **options):
        super(Testplan, self).__init__(**options)
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
        self._parsed_args = self.parser.parse_args()
        self._processed_args = self.parser.process_args(self._parsed_args)
        for key, value in self._processed_args.items():
            options.setdefault(key, value)

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
