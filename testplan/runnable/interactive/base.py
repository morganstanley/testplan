"""
Interactive handler for TestRunner runnable class.
"""
from __future__ import unicode_literals
from __future__ import print_function
from __future__ import division
from __future__ import absolute_import
from builtins import super
from builtins import next
from future import standard_library

standard_library.install_aliases()
import functools
import re
import six
import numbers
import threading
import itertools
from concurrent import futures
import contextlib

from testplan.common import entity
from testplan.common import config
from testplan.common.utils import networking
import testplan.report
from testplan.runnable.interactive import http
from testplan.runners.base import Executor
from testplan.runnable.interactive.reloader import ModuleReloader
from testplan.runnable.interactive.resource_loader import ResourceLoader


class TestRunnerIHandlerConfig(config.Config):
    """
    Configuration object for
    :py:class:`~testplan.runnable.interactive.base.TestRunnerIHandler` runnable
    interactive handler.
    """

    @classmethod
    def get_options(cls):
        return {"target": object, "startup_timeout": int, "http_port": int}


def _exclude_assertions_filter(obj):
    try:
        return obj["meta_type"] not in ("entry", "assertion")
    except Exception:
        return True


class TestRunnerIHandler(entity.Entity):
    """
    Runnable interactive handler for
    :py:class:`TestRunner <testplan.runnable.TestRunner>` runnable object.
    """

    CONFIG = TestRunnerIHandlerConfig
    STATUS = entity.RunnableStatus

    def __init__(self, target, startup_timeout=10, http_port=0):
        super(TestRunnerIHandler, self).__init__(
            target=target, startup_timeout=startup_timeout, http_port=http_port
        )
        self._cfg.parent = self.target.cfg

        self.report = self._initial_report()
        self.report_mutex = threading.Lock()
        self._pool = None
        self._http_handler = None

        self._created_environments = {}
        self._reloader = ModuleReloader(extra_deps=self.cfg.extra_deps)
        self._resource_loader = ResourceLoader()

    def __call__(self, *args, **kwargs):
        """
        Shortcut to setup, run the interactive handler until interrupted, then
        teardown.
        """
        self.setup()

        try:
            self.run()
        finally:
            self.teardown()

    def setup(self):
        """Set up the task pool and HTTP handler."""
        self.logger.test_info(
            "Starting {} for {}".format(self.__class__.__name__, self.target)
        )
        self._http_handler = self._setup_http_handler()
        self._pool = futures.ThreadPoolExecutor(max_workers=1)

    def run(self):
        """
        Setup and run the HTTP handler. Logs connection information to the
        terminal.
        """
        if self._pool is None or self._http_handler is None:
            raise RuntimeError("setup() not run")

        self.status.change(entity.RunnableStatus.RUNNING)
        self._display_connection_info()
        with self._pool:
            self._http_handler.run()
        self.status.change(entity.RunnableStatus.FINISHED)

    def teardown(self):
        """Close the task pool."""
        if self._pool is None or self._http_handler is None:
            raise RuntimeError("setup() not run")

        self._pool = None
        self._http_handler = None

    @property
    def http_handler_info(self):
        if self._http_handler is None:
            return None
        else:
            return self._http_handler.bind_addr

    @property
    def target(self):
        """
        :return: the target test runner instance
        """
        return self._cfg.target

    def abort_dependencies(self):
        """
        We abort our test runner instance.
        """
        yield self.target

    def aborting(self):
        """
        Do nothing when aborting.
        """
        pass

    def run_all_tests(self, runner_uid=None, await_results=True):
        """
        Run all tests.

        :param runner_uid: UID of a specific test runner, or None to use the
            default local runner.
        :param await_results: Whether to block until tests are finished,
            defaults to True.
        :return: If await_results is True, returns a testplan report.
            Otherwise, returns a future which will yield a testplan report when
            ready.
        """
        if not await_results:
            return self._run_async(self.run_all_tests, runner_uid)

        all_tests = self.all_tests(runner_uid)

        for test_uid, real_runner_uid in all_tests:
            self.run_test(test_uid, real_runner_uid)

    def run_test(self, test_uid, runner_uid=None, await_results=True):
        """
        Run a single Test instance.

        :param test_uid: UID of test to run.
        :param runner_uid: UID of a specific test runner, or None to use the
            default local runner.
        :param await_results: Whether to block until the test is finished,
            defaults to True.
        :return: If await_results is True, returns a test report.
            Otherwise, returns a future which will yield a test report when
            ready.
        """
        if not await_results:
            return self._run_async(self.run_test, test_uid, runner_uid)

        test = self.test(test_uid, runner_uid=runner_uid)

        try:
            self._auto_start_environment(test_uid, runner_uid)
        except RuntimeError:
            self.logger.exception("Failed to start environment for test.")
            with self.report_mutex:
                self.report[
                    test_uid
                ].runtime_status = testplan.report.RuntimeStatus.FINISHED
            return

        self._merge_testcase_reports(test.run_testcases_iter())

    def run_test_suite(
        self, test_uid, suite_uid, runner_uid=None, await_results=True
    ):
        """
        Run a single test suite.

        :param test_uid: UID of the test that owns the suite.
        :param suite_uid: UID of the suite to run.
        :param runner_uid: UID of a specific test runner, or None to use the
            default local runner.
        :param await_results: Whether to block until the suite is finished,
            defaults to True.
        :return: If await_results is True, returns a testsuite report.
            Otherwise, returns a future which will yield a testsuite report
            when ready.
        """
        if not await_results:
            return self._run_async(
                self.run_test_suite, test_uid, suite_uid, runner_uid
            )

        test = self.test(test_uid, runner_uid=runner_uid)

        try:
            self._auto_start_environment(test_uid, runner_uid)
        except RuntimeError:
            self.logger.exception("Failed to start environment for testsuite.")
            with self.report_mutex:
                self.report[test_uid][
                    suite_uid
                ].runtime_status = testplan.report.RuntimeStatus.FINISHED
            return

        self._merge_testcase_reports(
            test.run_testcases_iter(testsuite_pattern=suite_uid)
        )

    def run_test_case(
        self,
        test_uid,
        suite_uid,
        case_uid,
        runner_uid=None,
        await_results=True,
    ):
        """
        Run a single testcase.

        :param test_uid: UID of the test that owns the testcase.
        :param suite_uid: UID of the suite that owns the testcase.
        :param case_uid: UID of the testcase to run.
        :param runner_uid: UID of a specific test runner, or None to use the
            default local runner.
        :param await_results: Whether to block until the testcase is finished,
            defaults to True.
        :return: If await_results is True, returns a testcase report.
            Otherwise, returns a future which will yield a testcase report when
            ready.
        """
        if not await_results:
            return self._run_async(
                self.run_test_case, test_uid, suite_uid, case_uid, runner_uid
            )

        test = self.test(test_uid, runner_uid=runner_uid)

        try:
            self._auto_start_environment(test_uid, runner_uid)
        except RuntimeError:
            self.logger.exception("Failed to start environment for testcase.")
            with self.report_mutex:
                self.report[test_uid][suite_uid][
                    case_uid
                ].runtime_status = testplan.report.RuntimeStatus.FINISHED
            return

        self._merge_testcase_reports(
            test.run_testcases_iter(
                testsuite_pattern=suite_uid, testcase_pattern=case_uid
            )
        )

    def run_test_case_param(
        self,
        test_uid,
        suite_uid,
        case_uid,
        param_uid,
        runner_uid=None,
        await_results=True,
    ):
        """
        Run a single parametrization of a testcase.

        :param test_uid: UID of the test that owns the testcase.
        :param suite_uid: UID of the suite that owns the testcase.
        :param case_uid: UID of the testcase to run.
        :param param_uid: UID of the parametrization to run.
        :param runner_uid: UID of a specific test runner, or None to use the
            default local runner.
        :param await_results: Whether to block until the testcase is finished,
            defaults to True.
        :return: If await_results is True, returns a testcase report.
            Otherwise, returns a future which will yield a testcase report when
            ready.
        """
        if not await_results:
            return self._run_async(
                self.run_test_case_param,
                test_uid,
                suite_uid,
                case_uid,
                param_uid,
                runner_uid,
            )

        test = self.test(test_uid, runner_uid=runner_uid)

        try:
            self._auto_start_environment(test_uid, runner_uid)
        except RuntimeError:
            self.logger.exception("Failed to start environment for testcase.")
            with self.report_mutex:
                self.report[test_uid][suite_uid][case_uid][
                    param_uid
                ].runtime_status = testplan.report.RuntimeStatus.FINISHED
            return

        self._merge_testcase_reports(
            test.run_testcases_iter(
                testsuite_pattern=suite_uid, testcase_pattern=param_uid
            )
        )

    def test(self, test_uid, runner_uid=None):
        """
        Get a test instance with the specified UID.

        :param test_uid: UID of test to find.
        :param runner_uid: UID of test runner that owns the test, or None to
            specify the default local runner.
        """
        if runner_uid is None:
            runner = self.target.resources.local_runner
        else:
            runner = getattr(self.target.resources, runner_uid)
            if not isinstance(runner, Executor):
                raise RuntimeError(
                    "Invalid runner executor: {}".format(runner_uid)
                )
        item = runner.added_item(test_uid)
        return item

    def start_test_resources(
        self, test_uid, runner_uid=None, await_results=True
    ):
        """
        Start all test resources.

        :param test_uid: UID of test to start resources for
        :param runner_uid: UID of test runner that owns the test, or None to
            specify the default local runner.
        :param await_results: Whether to block until the test resources have
            all started, defaults to True.
        :return: If await_results is True, returns a list of the return values
            of each resource start operation, otherwise returns a list of async
            result objects.
        """
        if not await_results:
            return self._run_async(
                self.start_test_resources, test_uid, runner_uid
            )

        with self.report_mutex:
            self.report[test_uid].env_status = entity.ResourceStatus.STARTING

        test = self.test(test_uid, runner_uid=runner_uid)
        test.resources.start()

        with self.report_mutex:
            self.report[test_uid].env_status = entity.ResourceStatus.STARTED

    def stop_test_resources(
        self, test_uid, runner_uid=None, await_results=True
    ):
        """
        Stop all test resources.

        :param test_uid: UID of test to stop resources for
        :param runner_uid: UID of test runner that owns the test, or None to
            specify the default local runner.
        :param await_results: Whether to block until the test resources have
            all stopped, defaults to True.
        :return: If await_results is True, returns a list of the return values
            of each resource stop operation, otherwise returns a list of async
            result objects.
        """
        if not await_results:
            return self._run_async(
                self.stop_test_resources, test_uid, runner_uid
            )

        with self.report_mutex:
            self.report[test_uid].env_status = entity.ResourceStatus.STOPPING

        test = self.test(test_uid, runner_uid=runner_uid)
        test.resources.stop(reversed=True)

        with self.report_mutex:
            self.report[test_uid].env_status = entity.ResourceStatus.STOPPED

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

    def test_resource(self, test_uid, resource_uid, runner_uid=None):
        """Get a resource of a Test instance."""
        test = self.test(test_uid, runner_uid=runner_uid)
        return test.resources[resource_uid]

    def test_report(
        self,
        test_uid,
        runner_uid=None,
        serialized=True,
        exclude_assertions=False,
    ):
        """Get a test report."""
        test = self.test(test_uid, runner_uid=runner_uid)
        report = test.result.report
        if exclude_assertions is True:
            report = report.filter(_exclude_assertions_filter)
        if serialized:
            return report.serialize(strict=False)
        return report

    def test_case_report(
        self, test_uid, suite_uid, case_uid, runner_uid=None, serialized=True
    ):
        """Get a testcase report."""
        report = self.test_report(
            test_uid, runner_uid=runner_uid, serialized=False
        )

        def is_assertion(obj):
            try:
                return obj["meta_type"] in ("entry", "assertion")
            except Exception:
                return False

        def case_filter(obj):
            try:
                if obj.uid == case_uid:
                    return True
                return obj.uid == suite_uid or (
                    obj.category == "parametrization"
                    and any(entry.uid == case_uid for entry in obj.entries)
                )
            except Exception:
                return False

        report = report.filter(case_filter, is_assertion)
        if serialized:
            return report.serialize(strict=False)
        return report

    def start_environment(self, env_uid):
        """Start the specified environment."""
        env = self.get_environment(env_uid)
        env.start()
        return {item.uid(): item.status.tag for item in env}

    def stop_environment(self, env_uid):
        """Stop the specified environment."""
        env = self.get_environment(env_uid)
        env.stop(reversed=True)
        return {item.uid(): item.status.tag for item in env}

    def start_resource(self, resource):
        """Start a resource."""
        resource.start()
        resource._wait_started()

    def stop_resource(self, resource):
        """Stop a resource."""
        resource.stop()
        resource._wait_stopped()

    def test_resource_operation(
        self, test_uid, resource_uid, operation, runner_uid=None, **kwargs
    ):
        """Perform an operation on a test environment resource."""
        test = self.test(test_uid, runner_uid=runner_uid)
        resource = getattr(test.resources, resource_uid)
        func = getattr(resource, operation)
        return func(**kwargs)

    def test_resource_start(self, test_uid, resource_uid, runner_uid=None):
        """Start a resource of a Test instance."""
        resource = self.test_resource(
            test_uid, resource_uid, runner_uid=runner_uid
        )
        self.start_resource(resource)

    def test_resource_stop(self, test_uid, resource_uid, runner_uid=None):
        """Stop a resource of a Test instance."""
        resource = self.test_resource(
            test_uid, resource_uid, runner_uid=runner_uid
        )
        self.stop_resource(resource)

    def get_environment_context(
        self,
        env_uid,
        resource_uid=None,
        exclude_callables=True,
        exclude_protected=True,
        exclude_private=True,
    ):
        """Get the context information of an environment."""
        env = self.get_environment(env_uid)
        result = {}
        for item in env:
            if resource_uid is not None and item.uid() != resource_uid:
                continue
            result[item.uid()] = {}
            for key, value in item.context_input().items():
                if key == "context":
                    continue
                if exclude_private and key.startswith("__"):
                    continue
                if exclude_protected and key.startswith("_"):
                    # This excludes privates as well
                    continue
                if exclude_callables and callable(value):
                    continue
                if isinstance(value, (six.string_types, numbers.Number)):
                    result[item.uid()][key] = value
        if not result:
            if resource_uid is None:
                raise ValueError("No result for {}".format(env_uid))
            raise ValueError(
                "No result for {}{}".format(env_uid, resource_uid)
            )
        return result

    def environment_resource_context(
        self, env_uid, resource_uid, context_item=None, **kwargs
    ):
        """Get the context info of an environment resource."""
        result = self.get_environment_context(
            env_uid=env_uid, resource_uid=resource_uid, **kwargs
        )[resource_uid]
        if context_item:
            return result[context_item]
        return result

    def environment_resource_start(self, env_uid, resource_uid):
        """Start an environment resource."""
        resource = self.get_environment_resource(env_uid, resource_uid)
        self.start_resource(resource)

    def environment_resource_stop(self, env_uid, resource_uid):
        """Stop an environment resource."""
        resource = self.get_environment_resource(env_uid, resource_uid)
        self.stop_resource(resource)

    def environment_resource_operation(
        self, env_uid, resource_uid, res_op, **kwargs
    ):
        """Perform an operation on an environment resource."""
        if hasattr(self, "environment_resource_{}".format(res_op)):
            method = getattr(self, "environment_resource_{}".format(res_op))
            return method(env_uid, resource_uid, **kwargs)
        else:
            resource = self.get_environment_resource(env_uid, resource_uid)
            func = getattr(resource, res_op)
            return func(**kwargs)

    def all_tests(self, runner_uid=None):
        """Get all added tests."""
        for runner in self.target.resources:
            if runner_uid is None or runner_uid == runner.uid():
                if not isinstance(runner, Executor):
                    continue
                for test_uid in runner.added_items:
                    yield test_uid, runner.uid()

    def start_tests(self, runner_uid=None):
        """Start all tests environments."""
        self.all_tests_operation("start", runner_uid=runner_uid)

    def stop_tests(self, runner_uid=None):
        """Stop all tests environments."""
        self.all_tests_operation("stop", runner_uid=runner_uid)

    def all_tests_operation(
        self, operation, runner_uid=None, await_results=True
    ):
        """Perform an operation in all tests."""
        test_found = False
        all_tests = self.all_tests(runner_uid)
        while self.active and self.target.active:
            try:
                test_uid, real_runner_uid = next(all_tests)
            except StopIteration:
                break
            else:
                self.logger.debug(
                    "Operation {} for test: {} from {}".format(
                        operation, test_uid, real_runner_uid
                    )
                )
                if operation == "run":
                    self.run_test(
                        test_uid,
                        runner_uid=runner_uid,
                        await_results=await_results,
                    )
                elif operation == "start":
                    self.start_test_resources(test_uid, runner_uid=runner_uid)
                elif operation == "stop":
                    self.stop_test_resources(test_uid, runner_uid=runner_uid)
                else:
                    raise ValueError("Unknown operation: {}".format(operation))
                test_found = True
        if test_found is False:
            self.logger.test_info(
                "No tests found for runner: {}".format(runner_uid)
            )

    def create_new_environment(self, env_uid, env_type="local_environment"):
        """Dynamically create an environment maker object."""
        if env_uid in self._created_environments:
            raise RuntimeError(
                "Environment {} already exists.".format(env_uid)
            )

        if env_type == "local_environment":
            from testplan.environment import LocalEnvironment

            env_class = LocalEnvironment
        else:
            raise ValueError("Unknown environment type: {}".format(env_type))

        self._created_environments[env_uid] = env_class(env_uid)

    def add_environment_resource(
        self, env_uid, target_class_name, source_file=None, **kwargs
    ):
        """
        Add a resource to existing environment or to environment maker object.
        """
        final_kwargs = {}
        compiled = re.compile(r"_ctx_(.+)_ctx_(.+)")
        context_params = {}
        for key, value in kwargs.items():
            if key.startswith("_ctx_"):
                matched = compiled.match(key)
                if not matched or key.count("_ctx_") != 2:
                    raise ValueError("Invalid key: {}".format(key))
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
            resource = self._resource_loader.load(
                target_class_name, final_kwargs
            )
            try:
                self.get_environment(env_uid).add(resource)
            except:
                self._created_environments[env_uid].add_resource(resource)
        else:
            raise Exception("Add from source file is not yet supported.")

    def reload_environment_resource(
        self, env_uid, target_class_name, source_file=None, **kwargs
    ):
        # Placeholder for function to delele an existing and registering a new
        # environment resource with probably altered source code.
        # This should access the already added Environment to plan.
        pass

    def add_created_environment(self, env_uid):
        """Add an environment from the created environment maker instance."""
        self.target.add_environment(self._created_environments[env_uid])

    def reload(self, rebuild_dependencies=False):
        """Reload test suites."""
        tests = (
            self.test(test, runner_uid=runner_uid)
            for test, runner_uid in self.all_tests()
        )
        self._reloader.reload(tests, rebuild_dependencies)

    def _setup_http_handler(self):
        """
        Initialises the interactive HTTP handler.

        :return: Initialised HTTP handler.
        """
        self.logger.debug(
            "Setting up interactive HTTP handler to listen on port %d",
            self.cfg.http_port,
        )
        http_handler = http.TestRunnerHTTPHandler(
            ihandler=self, port=self.cfg.http_port
        )
        http_handler.cfg.parent = self.cfg
        http_handler.setup()

        return http_handler

    def _display_connection_info(self):
        """
        Log information for how to connect to the interactive runner.
        Currently only the API is implemented so we log how to access the
        API schema. In future we will log how to access the UI page.
        """
        host, port = self.http_handler_info

        self.logger.test_info(
            "\nInteractive Testplan API is running. View the API schema:\n%s",
            networking.format_access_urls(host, port, "/api/v1/interactive/"),
        )
        self.logger.critical(
            "\nInteractive Testplan web UI is running. Access it at:\n%s",
            networking.format_access_urls(host, port, "/interactive/"),
        )

    def _initial_report(self):
        """Generate the initial report skeleton."""
        report = testplan.report.TestReport(
            name=self.cfg.name, uid=self.cfg.name
        )

        for test_uid, runner_uid in self.all_tests():
            test = self.test(test_uid, runner_uid=runner_uid)
            test_report = test.dry_run().report
            report.append(test_report)

        return report

    def _run_all_test_operations(self, test_run_generator):
        """Run all test operations."""
        return [
            self._run_test_operation(operation, args, kwargs)
            for operation, args, kwargs in test_run_generator
        ]

    def _run_test_operation(self, test_operation, args, kwargs):
        """Run a test operation and update our report tree with the results."""
        result = test_operation(*args, **kwargs)

        if isinstance(result, testplan.report.TestGroupReport):
            self.logger.debug("Merge test result: %s", result)
            with self.report_mutex:
                self.report[result.uid].merge(result)
        elif result is not None:
            self.logger.debug(
                "Discarding result from test operation: %s", result
            )
        return result

    def _auto_start_environment(self, test_uid, runner_uid):
        """Start environment if required."""
        env_status = self.report[test_uid].env_status
        if env_status == entity.ResourceStatus.STOPPED:
            self.start_test_resources(test_uid, runner_uid)
        elif env_status != entity.ResourceStatus.STARTED:
            raise RuntimeError(
                "Cannot auto-start environment in state {}".format(env_status)
            )

    def _set_env_status(self, test_uid, new_status):
        """Set the environment status for a given test."""
        with self.report_mutex:
            self.logger.debug(
                "Setting env status of %s to %s", test_uid, new_status
            )
            self.report[test_uid].env_status = new_status

    def _run_async(self, func, *args, **kwargs):
        """
        Schedule a function to run asynchronously in our task pool. We add a
        callback to ensure that all async exceptions are logged, for debugging
        purposes.
        """
        future = self._pool.submit(func, *args, **kwargs)
        future.add_done_callback(self._log_async_exceptions)
        return future

    def _log_async_exceptions(self, future):
        """Log any exceptions that occur while running async."""
        try:
            future.result()
        except Exception:
            self.logger.exception("Exception caught in async function")

    def _merge_testcase_reports(self, testcase_reports):
        """Merge all test reports from a test run into our report."""
        for report, parent_uids in testcase_reports:
            self.logger.debug(
                "Merging testcase report %s with parent UIDs %s",
                report,
                parent_uids,
            )

            with self.report_mutex:
                parent_entry = self.report
                for uid in parent_uids:
                    parent_entry = parent_entry[uid]

                parent_entry[report.uid] = report
