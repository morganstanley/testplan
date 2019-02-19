"""
Interactive handler for TestRunner runnable class.
"""
import functools
import re

from testplan.common.config import ConfigOption
from testplan.common.entity import (RunnableIHandler, RunnableIHandlerConfig,
                                    ResourceStatus)
from testplan.report.testing import TestReport
from testplan.runnable.interactive.http import TestRunnerHTTPHandler
from testplan.runners.base import Executor
from testplan.runnable.interactive.reloader import ModuleReloader


class TestRunnerIHandlerConfig(RunnableIHandlerConfig):
    """
    Configuration object for
    :py:class:`~testplan.runnable.interactive.TestRunnerIHandler` runnable
    interactive handler.
    """
    @classmethod
    def get_options(cls):
        return {ConfigOption('http_handler',
                             default=TestRunnerHTTPHandler): object}


def _exclude_assertions_filter(obj):
    try:
        return obj['meta_type'] not in ('entry', 'assertion')
    except Exception:
        return True


def auto_start_stop_environment(method):
    """Auto start environment decorator logic."""
    @functools.wraps(method)
    def wrapped(self, test_uid, *args, **kwargs):
        """
        1. If the environment is not started -> Start it.
        2. Run the method.
        3. If the environment started during this operation. -> Stop it.
        """
        runner_uid = kwargs.get('runner_uid')
        test = self.test(test_uid, runner_uid=runner_uid)

        resources_started = False
        if not test.resources.all_status(ResourceStatus.STARTED):
            if not test.resources.all_status(ResourceStatus.STOPPED) and \
                  not test.resources.all_status(ResourceStatus.NONE):
                # State requires to reset all.
                self.stop_test_resources(test_uid, runner_uid=runner_uid)
            self.reset_test_report(test_uid, runner_uid=runner_uid)
            self.start_test_resources(test_uid, runner_uid=runner_uid)
            resources_started = True

        method(self, test_uid, *args, **kwargs)

        if resources_started is True:
            self.stop_test_resources(test_uid, runner_uid=runner_uid)

    return wrapped


class TestRunnerIHandler(RunnableIHandler):
    """
    Runnable intective handler for
    :py:class:`TestRunner <testplan.runnable.TestRunner>` runnable object.

    :param http_handler: Http requests handler to be used.
    :type http_handler: Subclass of
      :py:class:`~testplan.runnable.http.TestRunnerHTTPHandler`.

    Also inherits all
    :py:class:`~testplan.common.entity.base.RunnableIHandler` options.
    """
    CONFIG = TestRunnerIHandlerConfig

    def __init__(self, **options):
        super(TestRunnerIHandler, self).__init__(**options)
        self._created_environments = {}
        self._reloader = ModuleReloader(logger=self.logger,
                                        extra_deps=self.cfg.extra_deps)

    def _execute_operations(self, generator):
        while self.active and self.target.active:
            try:
                operation, args, kwargs = next(generator)
            except StopIteration:
                break
            else:
                op_id = self.add_operation(operation, *args, **kwargs)
                res = self._wait_result(op_id)
                self.logger.debug('Operation result: {}'.format(res))

    def report(self, serialized=False):
        """Get the top level Test report."""
        report = TestReport(name=self.cfg.name, uid=self.cfg.name)
        all_tests = self.all_tests()
        while self.active and self.target.active:
            try:
                test_uid, real_runner_uid = next(all_tests)
            except StopIteration:
                break
            else:
                test = self.test(test_uid, runner_uid=real_runner_uid)
                report.append(test.result.report)
        if serialized is True:
            return report.serialize()
        return report

    def get_environment(self, env_uid):
        """Get an environment."""
        return self.target.resources.environments[env_uid]

    def get_environment_resource(self, env_uid, resource_uid):
        """Get a resource from an environment."""
        return self.target.resources.environments[env_uid][resource_uid]

    def get_resource(self, runner_uid=None):
        """Get a runner resource."""
        if runner_uid is None:
            return self.target.resources.local_runner
        else:
            return getattr(self.target.resources, runner_uid)

    def test(self, test_uid, runner_uid=None):
        """Get a test instance from an executor holder."""
        if runner_uid is None:
            runner = self.target.resources.local_runner
        else:
            runner = getattr(self.target.resources, runner_uid)
            if not isinstance(runner, Executor):
                raise RuntimeError(
                    'Invalid runner executor: {}'.format(runner_uid))
        item = runner.added_item(test_uid)
        return item

    def test_resource(self, test_uid, resource_uid, runner_uid=None):
        """Get a resource of a Test instance."""
        test = self.test(test_uid, runner_uid=runner_uid)
        return test.resources[resource_uid]

    def test_report(self, test_uid, runner_uid=None, serialized=True,
                    exclude_assertions=False):
        """Get a test report."""
        test = self.test(test_uid, runner_uid=runner_uid)
        report = test.result.report
        if exclude_assertions is True:
            report = report.filter(_exclude_assertions_filter)
        if serialized is True:
            return report.serialize(strict=False)
        return report

    def test_case_report(self, test_uid, suite_uid, case_uid, runner_uid=None,
                         serialized=True):
        """Get a testcase report."""
        report = self.test_report(test_uid, runner_uid=runner_uid,
                                  serialized=False)

        def is_assertion(obj):
            try:
                return obj['meta_type'] in ('entry', 'assertion')
            except Exception:
                return False

        def case_filter(obj):
            try:
                if obj.uid == case_uid:
                    return True
                return obj.uid == suite_uid or \
                       (obj.category == 'parametrization' and
                        any(entry.uid == case_uid for entry in obj.entries))
            except Exception:
                return False

        report = report.filter(case_filter, is_assertion)
        if serialized is True:
            return report.serialize(strict=False)
        return report

    def start_environment(self, env_uid):
        """Start the specified environment."""
        env = self.get_environment(env_uid)
        op_id = self.add_operation(env.start)
        self._wait_result(op_id)
        return {item.uid(): item.status.tag for item in env}

    def stop_environment(self, env_uid):
        """Stop the specified environment."""
        env = self.get_environment(env_uid)
        op_id = self.add_operation(env.stop, reversed=True)
        self._wait_result(op_id)
        return {item.uid(): item.status.tag for item in env}

    def start_resource(self, resource):
        """Start a resource."""
        op_id = self.add_operation(resource.start)
        self._wait_result(op_id)
        op_id = self.add_operation(resource._wait_started)
        self._wait_result(op_id)

    def stop_resource(self, resource):
        """Stop a resource."""
        op_id = self.add_operation(resource.stop)
        self._wait_result(op_id)
        op_id = self.add_operation(resource._wait_stopped)
        self._wait_result(op_id)

    def test_resource_start(self, test_uid, resource_uid, runner_uid=None):
        """Start a resource of a Test instance."""
        resource = self.test_resource(
            test_uid, resource_uid, runner_uid=runner_uid)
        self.start_resource(resource)

    def test_resource_stop(self, test_uid, resource_uid, runner_uid=None):
        """Stop a resource of a Test instance."""
        resource = self.test_resource(
            test_uid, resource_uid, runner_uid=runner_uid)
        self.stop_resource(resource)

    def get_environment_context(self, env_uid,
                            resource_uid=None, exclude_callables=True,
                            exclude_protected=True, exclude_private=True):
        """Get the context information of an environment."""
        env = self.get_environment(env_uid)
        result = {}
        for item in env:
            if resource_uid is not None and item.uid() != resource_uid:
                continue
            result[item.uid()] = {}
            for key, value in item.context_input().items():
                if key == 'context':
                    continue
                if exclude_private and key.startswith('__'):
                    continue
                if exclude_protected and key.startswith('_'):
                    # This excludes privates as well
                    continue
                if exclude_callables and callable(value):
                    continue
                result[item.uid()][key] = value
        if not result:
            if resource_uid is None:
                raise ValueError('No result for {}'.format(env_uid))
            raise ValueError('No result for {}{}'.format(env_uid, resource_uid))
        return result

    def environment_resource_context(self, env_uid, resource_uid, **kwargs):
        """Get the context info of an environment resource."""
        return self.get_environment_context(
            env_uid=env_uid, resource_uid=resource_uid, **kwargs)[resource_uid]

    def environment_resource_start(self, env_uid, resource_uid):
        """Start an environment resource."""
        resource = self.get_environment_resource(env_uid, resource_uid)
        self.start_resource(resource)

    def environment_resource_stop(self, env_uid, resource_uid):
        """Stop an environment resource."""
        resource = self.get_environment_resource(env_uid, resource_uid)
        self.stop_resource(resource)

    def environment_resource_operation(self, env_uid, resource_uid,
                                       operation, **kwargs):
        """Perform an operation on an environment resource."""
        if hasattr(self, 'environment_resource_{}'.format(operation)):
            method = getattr(self, 'environment_resource_{}'.format(operation))
            return method(env_uid, resource_uid, **kwargs)
        else:
            resource = self.get_environment_resource(env_uid, resource_uid)
            op_id = self.add_operation(getattr(resource, operation), **kwargs)
            return self._wait_result(op_id)

    def start_test_resources(self, test_uid, runner_uid=None):
        """Start all test resources."""
        test = self.test(test_uid, runner_uid=runner_uid)
        test_irunner = test.cfg.interactive_runner(test)
        self._execute_operations(test_irunner.start_resources())

    def stop_test_resources(self, test_uid, runner_uid=None):
        """Stop all test resources."""
        test = self.test(test_uid, runner_uid=runner_uid)
        test_irunner = test.cfg.interactive_runner(test)
        self._execute_operations(test_irunner.stop_resources())

    def reset_test_report(self, test_uid, runner_uid=None):
        """Reset a Test instance report."""
        test = self.test(test_uid, runner_uid=runner_uid)
        test_irunner = test.cfg.interactive_runner(test)
        test_dry_run_generator = test_irunner.dry_run()
        operation, args, kwargs = next(test_dry_run_generator)
        op_id = self.add_operation(operation, *args, **kwargs)
        _ = self._wait_result(op_id)

    def reset_reports(self, runner_uid=None):
        """Reset all tests reports."""
        all_tests = self.all_tests(runner_uid)
        while self.active and self.target.active:
            try:
                test_uid, real_runner_uid = next(all_tests)
            except StopIteration:
                break
            else:
                self.reset_test_report(test_uid, runner_uid=real_runner_uid)

    @auto_start_stop_environment
    def run_test_case(self, test_uid, suite_uid, case_uid, runner_uid=None):
        """Run a single test case."""
        test = self.test(test_uid, runner_uid=runner_uid)
        irunner = test.cfg.interactive_runner(test)

        test_run_generator = irunner.run(suite=suite_uid, case=case_uid)
        while self.active and self.target.active:
            try:
                operation, args, kwargs = next(test_run_generator)
            except StopIteration:
                break
            else:
                op_id = self.add_operation(operation, *args, **kwargs)
                self._wait_result(op_id)

    @auto_start_stop_environment
    def run_test_suite(self, test_uid, suite_uid, runner_uid=None):
        """
        Run a single test suite.
        """
        test = self.test(test_uid, runner_uid=runner_uid)
        irunner = test.cfg.interactive_runner(test)

        test_run_generator = irunner.run(suite=suite_uid)
        while self.active and self.target.active:
            try:
                operation, args, kwargs = next(test_run_generator)
            except StopIteration:
                break
            else:
                op_id = self.add_operation(operation, *args, **kwargs)
                self._wait_result(op_id)

    @auto_start_stop_environment
    def run_test(self, test_uid, runner_uid=None):
        """Run a Test instance."""
        test = self.test(test_uid, runner_uid=runner_uid)
        irunner = test.cfg.interactive_runner(test)

        test_run_generator = irunner.run()
        while self.active and self.target.active:
            try:
                operation, args, kwargs = next(test_run_generator)
            except StopIteration:
                break
            else:
                op_id = self.add_operation(operation, *args, **kwargs)
                self._wait_result(op_id)

    def all_tests(self, runner_uid=None):
        """Get all added tests."""
        for runner in self.target.resources:
            if runner_uid is None or runner_uid == runner.uid():
                if not isinstance(runner, Executor):
                    continue
                for test_uid in runner.added_items:
                    yield test_uid, runner.uid()

    def run_tests(self, runner_uid=None):
        """Run all tests."""
        self.all_tests_operation('run', runner_uid=runner_uid)

    def start_tests(self, runner_uid=None):
        """Start all tests environments."""
        self.all_tests_operation('start', runner_uid=runner_uid)

    def stop_tests(self, runner_uid=None):
        """Stop all tests environments."""
        self.all_tests_operation('stop', runner_uid=runner_uid)

    def all_tests_operation(self, operation, runner_uid=None):
        """Perform an operation in all tests."""
        test_found = False
        all_tests = self.all_tests(runner_uid)
        while self.active and self.target.active:
            try:
                test_uid, real_runner_uid = next(all_tests)
            except StopIteration:
                break
            else:
                self.logger.debug('Operation {} for test: {} from {}'.format(
                    operation, test_uid, real_runner_uid))
                if operation == 'run':
                    self.run_test(
                        test_uid, runner_uid=runner_uid)
                elif operation == 'start':
                    self.start_test_resources(
                        test_uid, runner_uid=runner_uid)
                elif operation == 'stop':
                    self.stop_test_resources(
                        test_uid, runner_uid=runner_uid)
                else:
                    raise ValueError('Unknown operation: {}'.format(operation))
                test_found = True
        if test_found is False:
            self.logger.test_info(
                'No tests found for runner: {}'.format(runner_uid))

    def create_new_environment(self, env_uid, env_type='local_environment'):
        """Dynamically create an environment maker object."""
        if env_uid in self._created_environments:
            raise RuntimeError('Environment {} already exists.'.format(env_uid))

        if env_type == 'local_environment':
            from testplan.environment import LocalEnvironment
            env_class = LocalEnvironment
        else:
            raise ValueError('Unknown environment type: {}'.format(env_type))

        self._created_environments[env_uid] = env_class(env_uid)

    def add_environment_resource(self, env_uid, target_class_name,
                                 source_file=None, **kwargs):
        """Add a resource on the environment maker object."""
        final_kwargs = {}
        compiled = re.compile(r'_ctx_(.+)_ctx_(.+)')
        context_params = {}
        for key, value in kwargs.items():
            if key.startswith('_ctx_'):
                matched = compiled.match(key)
                if not matched or key.count('_ctx_') != 2:
                    raise ValueError('Invalid key: {}'.format(key))
                target_key, ctx_key = matched.groups()
                if target_key not in context_params:
                    context_params[target_key] = {}
                context_params[target_key][ctx_key] = value
            else:
                final_kwargs[key] = value
        if context_params:
            from testplan.common.utils.context import context
            for key in context_params:
                final_kwargs[key] = context(**context_params[key])

        if source_file is None:  # Invoke class loader
            from testplan.runnable.interactive.resource_loader import ResourceLoader
            target_class = ResourceLoader().load(target_class_name)
            resource = target_class(**final_kwargs)
            self._created_environments[env_uid].add_resource(resource)
        else:
            raise Exception('Add from source file is not yet supported.')

    def reload_environment_resource(self, env_uid, target_class_name,
                                    source_file=None, **kwargs):
        # Placeholder for function to delele an existing and registering a new
        # environment resource with probably altered source code.
        # This should access the already added Environment to plan.
        pass

    def add_created_environment(self, env_uid):
        """Add an environment from the created environment maker instance."""
        self.target.add_environment(self._created_environments[env_uid])

    def reload(self, rebuild_dependencies=True):
        """Reload test suites."""
        tests = (self.test(test, runner_uid=runner_uid)
                 for test, runner_uid in self.all_tests())
        self._reloader.reload(tests, rebuild_dependencies=rebuild_dependencies)
