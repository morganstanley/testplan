"""
Interactive handler for TestRunner runnable class.
"""
import numbers
import re
import socket
import threading
import warnings
from concurrent import futures
from typing import Awaitable, Dict, Optional, Union

from testplan.common import config, entity
from testplan.common.report import Report
from testplan.common.utils.networking import get_hostname_access_url
from testplan.report import (
    ReportCategories,
    RuntimeStatus,
    Status,
    TestGroupReport,
    TestReport,
)
from testplan.runnable.interactive import http, reloader, resource_loader


def _exclude_assertions_filter(obj: object) -> bool:
    try:
        return obj["meta_type"] not in ("entry", "assertion")
    except Exception:
        return True


class TestRunnerIHandlerConfig(config.Config):
    """
    Configuration object for
    :py:class:`~testplan.runnable.interactive.base.TestRunnerIHandler` runnable
    interactive handler.
    """

    @classmethod
    def get_options(cls):
        return {
            "target": lambda obj: isinstance(obj, entity.Runnable),
            config.ConfigOption("startup_timeout", default=10): int,
            config.ConfigOption("http_port", default=0): int,
        }


class TestRunnerIHandler(entity.Entity):
    """
    Runnable interactive handler for
    :py:class:`TestRunner <testplan.runnable.TestRunner>` runnable object.
    """

    CONFIG = TestRunnerIHandlerConfig
    STATUS = entity.RunnableStatus

    def __init__(
        self,
        target,
        startup_timeout=10,
        http_port=0,
        pre_start_environments=None,
    ):
        super(TestRunnerIHandler, self).__init__(
            target=target, startup_timeout=startup_timeout, http_port=http_port
        )
        self.cfg.parent = self.target.cfg
        self.parent = self.target
        self.report = self._initial_report()
        self.report_mutex = threading.Lock()
        self._pool = None
        self._http_handler = None
        self._created_environments = {}
        self.pre_start_environments = pre_start_environments

        try:
            self._reloader = reloader.ModuleReloader(
                extra_deps=getattr(self.cfg, "extra_deps", None),
                scheduled_modules=getattr(
                    self.parent, "scheduled_modules", None
                ),
            )
        except RuntimeError:
            self._reloader = None
        self._resource_loader = resource_loader.ResourceLoader()

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

    @property
    def target(self):
        """The test runner instance."""
        return self.cfg.target

    @property
    def exit_code(self):
        """Code to indicate success or failure."""
        return int(not self.report.passed)

    @property
    def exporters(self):
        return (
            self.parent.exporters if hasattr(self.parent, "exporters") else []
        )

    @property
    def http_handler_info(self):
        if self._http_handler is None:
            return None, None
        else:
            return self._http_handler.bind_addr

    def setup(self):
        """Set up the task pool and HTTP handler."""
        self.target.make_runpath_dirs()
        self.target._configure_file_logger()
        self.logger.info(
            "Starting %s for %s",
            self,
            self.target,
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
        if self.pre_start_environments is not None:
            for env in self.pre_start_environments:
                self.start_test_resources(env, await_results=False)
        self._display_connection_info()
        with self._pool:
            self._http_handler.run()
        self.status.change(entity.RunnableStatus.FINISHED)

    def aborting(self) -> None:
        """
        Aborting step for the handler. Stops resources before thread is joined.
        """
        for test_uid in self.all_tests():
            self.test(test_uid).stop_test_resources()

    def teardown(self):
        """Close the task pool."""
        self.logger.user_info("Stopping %s for %s", self, self.target)

        if self._pool is None or self._http_handler is None:
            raise RuntimeError("setup() not run")

        self.target._close_file_logger()
        self._pool = None
        self._http_handler = None

    def abort_dependencies(self):
        """Http service to be aborted at first."""
        yield self._http_handler

    def test(self, test_uid):
        """
        Get a test instance with the specified UID.

        :param test_uid: UID of test to find.
        """
        runner = self.target.resources[self.target.resources.first()]
        return runner.added_item(test_uid)

    def reset_all_tests(self, await_results=True):
        """
        Reset the Testplan report.

        :param await_results: Whether to block until tests are finished,
            defaults to True.
        :return: If await_results is True, returns a testplan report.
            Otherwise, returns a future which will yield a testplan report when
            ready.
        """
        if not await_results:
            return self._run_async(self.reset_all_tests)

        self.logger.debug("Interactive mode: Reset all tests")

        for test_uid in self.all_tests():
            self.reset_test(test_uid)

    def reset_test(self, test_uid, await_results=True):
        """
        Reset the report of a single Test instance.

        :param test_uid: UID of test to reset.
        :param await_results: Whether to block until tests are finished,
            defaults to True.
        :return: If await_results is True, returns a testplan report.
            Otherwise, returns a future which will yield a testplan report when
            ready.
        """
        if not await_results:
            return self._run_async(self.reset_test, test_uid)

        try:
            self._auto_stop_environment(test_uid)
        except RuntimeError as err:
            self.logger.exception(
                'Failed to stop environment for "%s": %s', test_uid, str(err)
            )
            # Should display error messages from the exception raised during
            # step `stop_test_resources` so will not regenerate test report
            self._update_reports(
                [({"runtime_status": RuntimeStatus.NOT_RUN}, [test_uid])]
            )
        else:
            self.logger.debug('Reset test ["%s"]', test_uid)
            # After reset the runtime_status will be 'READY'
            self._update_reports([(self.test(test_uid).dry_run().report, [])])

    def run_all_tests(
        self,
        shallow_report: Optional[Dict] = None,
        await_results: bool = True,
    ) -> Union[TestReport, Awaitable]:
        """
        Runs all tests.

        :param shallow_report: shallow report entry, optional
        :param await_results: Whether to block until tests are finished,
            defaults to True.
        :return: If await_results is True, returns a testplan report.
            Otherwise, returns a future which will yield a testplan report when
            ready.
        """
        if not await_results:
            return self._run_async(
                self.run_all_tests, shallow_report=shallow_report
            )

        if shallow_report:
            self.logger.debug("Interactive mode: Run filtered tests")
            for multitest in shallow_report["entries"]:
                self.run_test(
                    test_uid=multitest["name"], shallow_report=multitest
                )
        else:
            self.logger.debug("Interactive mode: Run all tests")
            for test_uid in self.all_tests():
                self.run_test(test_uid=test_uid)

    def run_test(
        self,
        test_uid: str,
        shallow_report: Optional[Dict] = None,
        await_results: bool = True,
    ) -> Union[TestReport, Awaitable]:
        """
        Run a single Test instance.

        :param test_uid: UID of test to run.
        :param shallow_report: shallow report entry, optional
        :param await_results: Whether to block until the test is finished,
            defaults to True.
        :return: If await_results is True, returns a test report.
            Otherwise, returns a future which will yield a test report when
            ready.
        """
        if not await_results:
            return self._run_async(
                self.run_test, test_uid, shallow_report=shallow_report
            )

        try:
            self._auto_start_environment(test_uid)
        except RuntimeError as err:
            self.logger.exception(
                'Failed to start environment for "%s": %s', test_uid, str(err)
            )
            self._update_reports(
                [({"runtime_status": RuntimeStatus.NOT_RUN}, [test_uid])]
            )
        else:
            self.logger.debug('Run test ["%s"]', test_uid)
            self._update_reports(
                self.test(test_uid).run_testcases_iter(
                    shallow_report=shallow_report
                )
            )

    def run_test_suite(
        self,
        test_uid: str,
        suite_uid: str,
        shallow_report: Optional[Dict] = None,
        await_results: bool = True,
    ) -> Union[TestReport, Awaitable]:
        """
        Run a single test suite.

        :param test_uid: UID of the test that owns the suite.
        :param suite_uid: UID of the suite to run.
        :param shallow_report: shallow report entry, optional
        :param await_results: Whether to block until the suite is finished,
            defaults to True.
        :return: If await_results is True, returns a testsuite report.
            Otherwise, returns a future which will yield a testsuite report
            when ready.
        """
        if not await_results:
            return self._run_async(
                self.run_test_suite,
                test_uid,
                suite_uid,
                shallow_report=shallow_report,
            )

        try:
            self._auto_start_environment(test_uid)
        except RuntimeError as err:
            self.logger.exception(
                'Failed to start environment for "%s": %s', test_uid, str(err)
            )
            self._update_reports(
                [
                    (
                        {"runtime_status": RuntimeStatus.NOT_RUN},
                        [test_uid, suite_uid],
                    )
                ]
            )
        else:
            self.logger.debug('Run suite ["%s" / "%s"]', test_uid, suite_uid)
            self._update_reports(
                self.test(test_uid).run_testcases_iter(
                    testsuite_pattern=suite_uid, shallow_report=shallow_report
                )
            )

    def run_test_case(
        self,
        test_uid: str,
        suite_uid: str,
        case_uid: str,
        shallow_report: Optional[Dict] = None,
        await_results: bool = True,
    ) -> Union[TestReport, Awaitable]:
        """
        Run a single testcase.

        :param test_uid: UID of the test that owns the testcase.
        :param suite_uid: UID of the suite that owns the testcase.
        :param case_uid: UID of the testcase to run.
        :param shallow_report: shallow report entry, optional
        :param await_results: Whether to block until the testcase is finished,
            defaults to True.
        :return: If await_results is True, returns a testcase report.
            Otherwise, returns a future which will yield a testcase report when
            ready.
        """
        if not await_results:
            return self._run_async(
                self.run_test_case,
                test_uid,
                suite_uid,
                case_uid,
                shallow_report=shallow_report,
            )

        try:
            self._auto_start_environment(test_uid)
        except RuntimeError as err:
            self.logger.exception(
                'Failed to start environment for "%s": %s', test_uid, str(err)
            )
            self._update_reports(
                [
                    (
                        {"runtime_status": RuntimeStatus.NOT_RUN},
                        [test_uid, suite_uid, test_uid],
                    )
                ]
            )
        else:
            self.logger.debug(
                'Run testcase or parametrization group ["%s" / "%s" / "%s"]',
                test_uid,
                suite_uid,
                case_uid,
            )
            self._update_reports(
                self.test(test_uid).run_testcases_iter(
                    testsuite_pattern=suite_uid,
                    testcase_pattern=case_uid,
                    shallow_report=shallow_report,
                )
            )

    def run_test_case_param(
        self,
        test_uid: str,
        suite_uid: str,
        case_uid: str,
        param_uid: str,
        shallow_report: Optional[Dict] = None,
        await_results: bool = True,
    ):
        """
        Run a single parametrization of a testcase.

        :param test_uid: UID of the test that owns the testcase.
        :param suite_uid: UID of the suite that owns the testcase.
        :param case_uid: UID of the testcase to run.
        :param param_uid: UID of the parametrization to run.
        :param shallow_report: shallow report entry, optional
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
                shallow_report=shallow_report,
            )

        try:
            self._auto_start_environment(test_uid)
        except RuntimeError as err:
            self.logger.exception(
                'Failed to start environment for "%s": %s', test_uid, str(err)
            )
            self._update_reports(
                [
                    (
                        {"runtime_status": RuntimeStatus.NOT_RUN},
                        [test_uid, suite_uid, test_uid, param_uid],
                    )
                ]
            )
        else:
            self.logger.debug(
                'Run testcase ["%s" / "%s" / "%s" / "%s"]',
                test_uid,
                suite_uid,
                case_uid,
                param_uid,
            )
            self._update_reports(
                self.test(test_uid).run_testcases_iter(
                    testsuite_pattern=suite_uid,
                    testcase_pattern=param_uid,
                    shallow_report=shallow_report,
                )
            )

    def start_test_resources(self, test_uid, await_results=True):
        """
        Start all test resources.

        :param test_uid: UID of test to start resources for
        :param await_results: Whether to block until the test resources have
            all started, defaults to True.
        :return: If await_results is True, returns a list of the return values
            of each resource start operation, otherwise returns a list of async
            result objects.
        """
        if not await_results:
            return self._run_async(self.start_test_resources, test_uid)

        self._set_env_status(test_uid, entity.ResourceStatus.STARTING)
        if self.report[test_uid].status_override == Status.ERROR:
            self._clear_env_errors(test_uid)
        self.test(test_uid).start_test_resources()

        exceptions = self.test(test_uid).resources.start_exceptions
        if exceptions:
            self._log_env_errors(test_uid, exceptions.values())
            self._set_env_status(test_uid, entity.ResourceStatus.STOPPED)
            raise RuntimeError(
                "Exception raised during starting drivers: {}".format(
                    ", ".join(str(driver) for driver in exceptions.keys())
                )
            )
        else:
            self._set_env_status(test_uid, entity.ResourceStatus.STARTED)

    def stop_test_resources(self, test_uid, await_results=True):
        """
        Stop all test resources.

        :param test_uid: UID of test to stop resources for
        :param await_results: Whether to block until the test resources have
            all stopped, defaults to True.
        :return: If await_results is True, returns a list of the return values
            of each resource stop operation, otherwise returns a list of async
            result objects.
        """
        if not await_results:
            return self._run_async(self.stop_test_resources, test_uid)

        self._set_env_status(test_uid, entity.ResourceStatus.STOPPING)
        if self.report[test_uid].status_override == Status.ERROR:
            self._clear_env_errors(test_uid)
        self.test(test_uid).stop_test_resources()

        exceptions = self.test(test_uid).resources.stop_exceptions
        if exceptions:
            self._log_env_errors(test_uid, exceptions.values())
            self._set_env_status(test_uid, entity.ResourceStatus.STOPPED)
            raise RuntimeError(
                "Exception raised during stopping drivers: {}".format(
                    ", ".join(str(driver) for driver in exceptions.keys())
                )
            )
        else:
            self._set_env_status(test_uid, entity.ResourceStatus.STOPPED)

    def get_environment(self, env_uid):
        """Get an environment."""
        return self.target.resources.environments[env_uid]

    def get_environment_resource(self, env_uid, resource_uid):
        """Get a resource from an environment."""
        return self.target.resources.environments[env_uid][resource_uid]

    def test_resource(self, test_uid, resource_uid):
        """Get a resource of a Test instance."""
        test = self.test(test_uid)
        return test.resources[resource_uid]

    def test_report(self, test_uid, serialized=True, exclude_assertions=False):
        """Get a test report."""
        test = self.test(test_uid)
        report = test.result.report
        if exclude_assertions is True:
            report = report.filter(_exclude_assertions_filter)
        if serialized:
            return report.serialize()
        return report

    def test_case_report(self, test_uid, suite_uid, case_uid, serialized=True):
        """Get a testcase report."""
        report = self.test_report(test_uid, serialized=False)

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
                    obj.category == ReportCategories.PARAMETRIZATION
                    and any(entry.uid == case_uid for entry in obj.entries)
                )
            except Exception:
                return False

        report = report.filter(case_filter, is_assertion)
        if serialized:
            return report.serialize()
        return report

    def start_environment(self, env_uid):
        """Start the specified environment."""
        env = self.get_environment(env_uid)
        env.start()
        return {item.uid(): item.status.tag for item in env}

    def stop_environment(self, env_uid):
        """Stop the specified environment."""
        env = self.get_environment(env_uid)
        env.stop(is_reversed=True)
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
        self, test_uid, resource_uid, operation, **kwargs
    ):
        """Perform an operation on a test environment resource."""
        test = self.test(test_uid)
        resource = getattr(test.resources, resource_uid)
        func = getattr(resource, operation)
        return func(**kwargs)

    def test_resource_start(self, test_uid, resource_uid):
        """Start a resource of a Test instance."""
        resource = self.test_resource(test_uid, resource_uid)
        self.start_resource(resource)

    def test_resource_stop(self, test_uid, resource_uid):
        """Stop a resource of a Test instance."""
        resource = self.test_resource(test_uid, resource_uid)
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
                if isinstance(value, (str, numbers.Number)):
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

    def all_tests(self):
        """Get all added tests."""
        try:
            runner = self.target.resources[self.target.resources.first()]
        except StopIteration:
            return
        for test_uid in runner.added_items:
            yield test_uid

    def start_tests(self):
        """Start all tests environments."""
        self.all_tests_operation("start")

    def stop_tests(self, runner_uid=None):
        """Stop all tests environments."""
        self.all_tests_operation("stop")

    def all_tests_operation(self, operation, await_results=True):
        """Perform an operation in all tests."""
        all_tests = self.all_tests()

        for test_uid in all_tests:
            if not (self.active and self.target.active):
                break
            self.logger.debug(
                "Operation %s for test: %s",
                operation,
                test_uid,
            )
            if operation == "run":
                self.run_test(test_uid, await_results=await_results)
            elif operation == "start":
                self.start_test_resources(test_uid)
            elif operation == "stop":
                self.stop_test_resources(test_uid)
            else:
                raise ValueError("Unknown operation: {}".format(operation))

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
        if self._reloader is None:
            raise RuntimeError("Reloader failed to initialize.")
        tests = (self.test(test) for test in self.all_tests())
        self._reloader.reload(tests, rebuild_dependencies)

    def reload_report(self):
        """Update report with added/removed testcases"""
        new_report = self._initial_report()
        for multitest in self.report.entries:  # multitest level
            for suite_index, suite in enumerate(multitest.entries):
                new_suite = new_report[multitest.uid][suite.uid]
                for case_index, case in enumerate(suite.entries):
                    try:
                        if isinstance(case, TestGroupReport):
                            for param_index, param_case in enumerate(
                                case.entries
                            ):
                                try:
                                    new_report[multitest.uid][suite.uid][
                                        case.uid
                                    ].entries[param_index] = case[
                                        param_case.uid
                                    ]
                                except KeyError:
                                    continue
                        else:
                            new_report[multitest.uid][suite.uid].entries[
                                case_index
                            ] = suite[case.uid]
                    except KeyError:
                        continue
                multitest.entries[suite_index] = new_suite

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

        # Mute flask_restx warning.
        with warnings.catch_warnings():
            warnings.filterwarnings("ignore")
            http_handler.setup()

        return http_handler

    def _display_connection_info(self):
        """
        Log information for how to connect to the interactive runner.
        Currently only the API is implemented so we log how to access the
        API schema. In future we will log how to access the UI page.
        """
        host, port = self.http_handler_info
        if host is None or port is None:
            raise RuntimeError(
                "Interactive Testplan web service is not available"
            )

        self.logger.user_info(
            "\nInteractive Testplan web UI is running. Access it at: %s",
            get_hostname_access_url(port, "/interactive"),
        )

    def _initial_report(self):
        """Generate the initial report skeleton."""
        report = TestReport(
            name=self.cfg.name,
            description=self.cfg.description,
            uid=self.cfg.name,
        )

        for test_uid in self.all_tests():
            test = self.test(test_uid)
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

        if isinstance(result, TestGroupReport):
            self.logger.debug("Merge test result: %s", result)
            with self.report_mutex:
                self.report[result.uid].merge(result)
        elif result is not None:
            self.logger.debug(
                "Discarding result from test operation: %s", result
            )
        return result

    def _auto_start_environment(self, test_uid):
        """Start environment if required."""
        env_status = self.report[test_uid].env_status

        if env_status is None:
            return
        elif env_status == entity.ResourceStatus.STOPPED:
            self.logger.debug('Auto start environment for "%s"', test_uid)
            self.start_test_resources(test_uid)
        elif env_status != entity.ResourceStatus.STARTED:
            raise RuntimeError(
                "Cannot auto start environment in state {}".format(env_status)
            )

    def _auto_stop_environment(self, test_uid):
        """Start environment if required."""
        env_status = self.report[test_uid].env_status

        if env_status is None:
            return
        elif env_status == entity.ResourceStatus.STARTED:
            self.logger.debug('Auto stop environment for "%s"', test_uid)
            self.stop_test_resources(test_uid)
        elif env_status != entity.ResourceStatus.STOPPED:
            raise RuntimeError(
                "Cannot auto stop environment in state {}".format(env_status)
            )

    def _set_env_status(self, test_uid, new_status):
        """Set the environment status for a given test."""
        with self.report_mutex:
            self.logger.debug(
                'Setting env status of "%s" to %s', test_uid, new_status
            )
            self.report[test_uid].env_status = new_status

    def _log_env_errors(self, test_uid, error_messages):
        """Log errors during environment start/stop for a given test."""
        test_report = self.report[test_uid]
        with self.report_mutex:
            for errmsg in error_messages:
                test_report.logger.error(errmsg)
            test_report.status_override = Status.ERROR

    def _clear_env_errors(self, test_uid):
        """Remove error logs about environment start/stop for a given test."""
        test = self.test(test_uid)
        test_report = self.report[test_uid]
        with self.report_mutex:
            test.resources.start_exceptions.clear()
            test.resources.stop_exceptions.clear()
            test_report.logs.clear()
            test_report.status_override = None

    def _run_async(self, func, *args, **kwargs) -> Awaitable:
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

    def _merge_report(self, report, parent_uids):
        """Merge test report from a test run."""
        with self.report_mutex:
            parent_entry = self.report
            for uid in parent_uids:
                parent_entry = parent_entry[uid]

            self.logger.debug(
                "Merging report %s with parent UIDs %s",
                report,
                parent_uids,
            )
            for attachment in report.attachments:
                self.report.attachments[
                    attachment.dst_path
                ] = attachment.source_path
            parent_entry[report.uid] = report

    def _merge_attributes(self, attribs, parent_uids):
        """Merge attributes of test report from a test run."""
        with self.report_mutex:
            parent_entry = self.report
            for uid in parent_uids:
                parent_entry = parent_entry[uid]

            self.logger.debug(
                "Merging attribute %s of report %s with parent UIDs %s",
                list(attribs.keys()),
                parent_entry,
                parent_uids[:-1],
            )
            for key, value in attribs.items():
                if hasattr(parent_entry, key):
                    setattr(parent_entry, key, value)

    def _update_reports(self, items):
        """Merges test report or attributes of test reports from a test run."""
        for item, parent_uids in items:
            if isinstance(item, Report):
                self._merge_report(item, parent_uids)
            elif isinstance(item, dict):
                self._merge_attributes(item, parent_uids)
            else:
                raise RuntimeError(
                    "Invalid item found for updating report: {}".format(item)
                )
