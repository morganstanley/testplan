"""Testplan base module."""
import argparse
import os
import random
import signal
import sys
import tempfile
import traceback
import threading

from typing import Optional, Union, Type, List, Callable
from types import ModuleType
from schema import And

from testplan import defaults
from testplan.common import entity
from testplan.common.config import ConfigOption
from testplan.common.utils import logger, path
from testplan.common.utils.callable import arity
from testplan.common.utils.logger import TESTPLAN_LOGGER
from testplan.common.utils.validation import has_method, is_subclass
from testplan.environment import Environments
from testplan.parser import TestplanParser
from testplan.runnable import TestRunner, TestRunnerConfig, TestRunnerResult
from testplan.runnable.interactive import TestRunnerIHandler
from testplan.runners.local import LocalRunner
from testplan.runners.base import Executor
from testplan.report.testing.styles import Style
from testplan.testing import filtering, ordering
from testplan.testing.filtering import BaseFilter
from testplan.testing.listing import MetadataBasedLister
from testplan.testing.multitest.test_metadata import TestPlanMetadata
from testplan.testing.ordering import BaseSorter


def pdb_drop_handler(sig, frame):
    """
    Drop into pdb
    """
    print("Received SIGUSR1, dropping into pdb")
    import pdb

    pdb.set_trace()


class TestplanConfig(entity.RunnableManagerConfig, TestRunnerConfig):
    """
    Configuration object for :py:class:`~testplan.base.Testplan` entity.
    """

    @classmethod
    def get_options(cls):
        """Additional and updated config options for Testplan class."""
        return {
            ConfigOption("parser", default=TestplanParser): And(
                has_method("parse_args"), has_method("process_args")
            ),
            ConfigOption("runnable", default=TestRunner): is_subclass(
                entity.Runnable
            ),
        }


class TestplanResult(TestRunnerResult):
    """
    Result object of a :py:class:`~testplan.base.Testplan`
    :py:class:`runnable manager <testplan.common.entity.base.RunnableManager>`
    entity.
    """

    def __init__(self) -> None:
        super(TestplanResult, self).__init__()
        self.decorated_value = None

    @property
    def exit_code(self) -> int:
        """System exit code based on successful run."""
        return 0 if getattr(self, "run", False) and self.success else 1

    def __bool__(self):
        """
        To be used by ``sys.exit(not main())`` pattern.
        """
        return True if self.exit_code == 0 else False


class Testplan(entity.RunnableManager):
    r"""
    A collection of tests and tests executors with the ability to
    selectively execute a subset or a shuffled set of those tests.

    It manages a
    :py:class:`~testplan.runnable.TestRunner` to execute the tests and also
    accepts all :py:class:`~testplan.common.entity.base.RunnableManagerConfig`
    and :py:class:`~testplan.runnable.TestRunnerConfig` options.

    Since it's a manager of a TestRunner object, it **exposes all**
    :py:class:`~testplan.runnable.TestRunner`,
    attributes and methods like
    :py:meth:`~testplan.runnable.TestRunner.add_resource`,
    :py:meth:`~testplan.runnable.TestRunner.add`, and
    :py:meth:`~testplan.runnable.TestRunner.schedule`.

    :param name: Name of test plan.
    :param description: Description of test plan.
    :param parse_cmdline: Parse command line arguments.
    :param parser: Command line parser.
    :param interactive_port: Enable interactive execution mode on a port.
    :param abort_signals: Signals to catch and trigger abort. By default,
        SIGINT and SIGTERM will trigger Testplan to abort.
    :param logger_level: Logger level for stdout.
    :param: file_log_level: Logger level for file.
    :param runpath: Input runpath.
    :param path_cleanup: Clean previous runpath entries.
    :param all_tasks_local: Schedule all tasks in local pool.
    :param shuffle: Shuffle strategy.
    :param shuffle_seed: Shuffle seed.
    :param exporters: Exporters for reports creation.
    :param stdout_style: Styling output options.
    :param report_dir: Report directory.
    :param xml_dir: XML output directory.
    :param json_path: JSON output path <PATH>/\*.json.
    :param http_url: HTTP url to post JSON report.
    :param pdf_path: PDF output path <PATH>/\*.pdf.
    :param pdf_style: PDF creation styling options.
    :param report_tags: Matches tests marked with any of the given tags.
    :param report_tags_all: Match tests marked with all of the given tags.
    :param resource_monitor: Enable resource monitor.
    :param merge_scheduled_parts: Merge reports of scheduled MultiTest
        parts.
    :param browse: Open web browser to display the test report.
    :param ui_port: Port of web server for displaying test report.
    :param web_server_startup_timeout: Timeout for starting web server.
    :param test_filter: Tests filtering class.
    :param test_sorter: Tests sorting class.
    :param test_lister: Tests listing class.
    :param test_lister_output: listing results goes to this file, if None goes to stdout
    :param verbose: Enable or disable verbose mode.
    :param debug: Enable or disable debug mode.
    :param timeout: Timeout value in seconds to kill Testplan and all child
        processes, default to 14400s(4h), set to 0 to disable.
    :param interactive_handler: Handler for interactive mode execution.
    :param extra_deps: Extra module dependencies for interactive reload, or
        paths of these modules.
    :param label: Label the test report with the given name, useful to
        categorize or classify similar reports .
    :param driver_info: Display driver setup / teardown time and driver
        interconnection information in UI report.
    :param collect_code_context: Collects the file path, line number and code
        context of the assertions.
    """

    CONFIG = TestplanConfig

    # NOTE: if adding, deleting or modifying a constructor parameter here you
    # MUST also update the class docstring above and main_wrapper entry point
    # below with the same change.
    def __init__(
        self,
        name: str,
        description: Optional[str] = None,
        parse_cmdline: bool = True,
        parser: Type[TestplanParser] = TestplanParser,
        interactive_port: Optional[int] = None,
        abort_signals: Optional[List[int]] = None,
        logger_level: int = logger.USER_INFO,
        file_log_level: int = logger.DEBUG,
        runpath: Union[str, Callable] = path.default_runpath,
        path_cleanup: bool = True,
        all_tasks_local: bool = False,
        shuffle: Optional[List[str]] = None,
        shuffle_seed: float = float(random.randint(1, 9999)),
        exporters: Optional[List] = None,
        stdout_style: Style = defaults.STDOUT_STYLE,
        report_dir: str = defaults.REPORT_DIR,
        xml_dir: Optional[str] = None,
        json_path: Optional[str] = None,
        http_url: Optional[str] = None,
        pdf_path: Optional[str] = None,
        pdf_style: Style = defaults.PDF_STYLE,
        report_tags: Optional[List] = None,
        report_tags_all: Optional[List] = None,
        resource_monitor: bool = False,
        merge_scheduled_parts: bool = False,
        browse: bool = False,
        ui_port: Optional[int] = None,
        web_server_startup_timeout: int = defaults.WEB_SERVER_TIMEOUT,
        test_filter: Type[BaseFilter] = filtering.Filter(),
        test_sorter: Type[BaseSorter] = ordering.NoopSorter(),
        test_lister: Optional[MetadataBasedLister] = None,
        test_lister_output: Optional[os.PathLike] = None,
        verbose: bool = False,
        debug: bool = False,
        timeout: int = defaults.TESTPLAN_TIMEOUT,
        interactive_handler: Type[TestRunnerIHandler] = TestRunnerIHandler,
        extra_deps: Optional[List[Union[str, ModuleType]]] = None,
        label: Optional[str] = None,
        driver_info: bool = False,
        collect_code_context: bool = False,
        auto_part_runtime_limit: int = defaults.AUTO_PART_RUNTIME_LIMIT,
        plan_runtime_target: int = defaults.PLAN_RUNTIME_TARGET,
        **options,
    ):

        # Set mutable defaults.
        if abort_signals is None:
            abort_signals = entity.DEFAULT_RUNNABLE_ABORT_SIGNALS[:]
        if shuffle is None:
            shuffle = []
        if extra_deps is None:
            extra_deps = []
        if report_tags is None:
            report_tags = []
        if report_tags_all is None:
            report_tags_all = []

        # Define instance attributes
        self._parsed_args = argparse.Namespace()
        self._processed_args = {}
        self._default_options = {}

        super(Testplan, self).__init__(
            name=name,
            description=description,
            parse_cmdline=parse_cmdline,
            parser=parser,
            interactive_port=interactive_port,
            abort_signals=abort_signals,
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
            json_path=json_path,
            http_url=http_url,
            pdf_path=pdf_path,
            pdf_style=pdf_style,
            report_tags=report_tags,
            report_tags_all=report_tags_all,
            resource_monitor=resource_monitor,
            merge_scheduled_parts=merge_scheduled_parts,
            browse=browse,
            ui_port=ui_port,
            web_server_startup_timeout=web_server_startup_timeout,
            test_filter=test_filter,
            test_sorter=test_sorter,
            test_lister=test_lister,
            test_lister_output=test_lister_output,
            verbose=verbose,
            debug=debug,
            timeout=timeout,
            interactive_handler=interactive_handler,
            extra_deps=extra_deps,
            label=label,
            driver_info=driver_info,
            collect_code_context=collect_code_context,
            auto_part_runtime_limit=auto_part_runtime_limit,
            plan_runtime_target=plan_runtime_target,
            **options,
        )

        # By default, a LocalRunner is added to store and execute the tests.
        self._runnable.add_resource(LocalRunner())

        # Stores independent environments.
        self._runnable.add_resource(Environments())

    @property
    def parser(self):
        """Returns a new command line parser."""
        return self._cfg.parser(
            name=self._cfg.name, default_options=self._default_options
        )

    @property
    def args(self):
        """Parsed arguments."""
        return self._parsed_args

    @property
    def processed_args(self):
        """Processed parsed arguments."""
        return self._processed_args

    def enrich_options(self, options):
        """
        Enrich the options using parsed command line arguments.
        The command line arguments will override any explicit programmatic
        declaration for a given keyword.
        """
        parser = self.parser
        self._parsed_args = parser.parse_args()
        self._processed_args = parser.process_args(self._parsed_args)
        for key in self._processed_args:
            options[key] = self._processed_args[key]
        return options

    def _print_current_status(self, sig, frame):
        """
        Print stack frames of all threads and status information of
        resources.
        """

        print("Received SIGUSR2, printing current status")
        id2name = dict(
            [(thread.ident, thread.name) for thread in threading.enumerate()]
        )

        msgs = ["Stack frames of all threads"]
        for thread_id, stack in sorted(
            sys._current_frames().items(), reverse=True
        ):
            msgs.append(
                f"{os.linesep}# Thread: {id2name.get(thread_id, '')}({thread_id})"
            )
            for filename, lineno, name, line in traceback.extract_stack(stack):
                msgs.append(f'File: "{filename}", line {lineno}, in {name}')
                if line:
                    msgs.append(f"  {line.strip()}")

        msg = os.linesep.join(msgs)
        print(msg)

        msgs = ["State of tests"]
        for resource in self.resources:
            if isinstance(resource, Executor):
                msgs.extend(resource.get_current_status_for_debug())

        msg = os.linesep.join(msgs)
        print(msg)

    def run(self):
        """
        Runs the tests added and returns the result object.
        Also handles usr1 and usr2 signals.

        :return: Result containing tests and execution steps results.
        :rtype: :py:class:`~testplan.base.TestplanResult`
        """
        try:
            if hasattr(signal, "SIGUSR1"):
                signal.signal(signal.SIGUSR1, pdb_drop_handler)
            if hasattr(signal, "SIGUSR2"):
                signal.signal(signal.SIGUSR2, self._print_current_status)
        except Exception:
            pass

        result = super(Testplan, self).run()
        if isinstance(result, TestRunnerResult):
            testplan_result = TestplanResult()
            testplan_result.__dict__ = result.__dict__
            return testplan_result
        return result

    # NOTE: if adding, deleting or modifying a wrapper parameter here you
    # MUST also update the class docstring and __init__() constructor above
    # with the same change. We have these parameters and their defaults
    # duplicated here in order to provide good IDE auto-complete experience
    # for users.
    @classmethod
    def main_wrapper(
        cls,
        name,
        description=None,
        parse_cmdline=True,
        parser=TestplanParser,
        interactive_port=None,
        abort_signals=None,
        logger_level=logger.USER_INFO,
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
        json_path=None,
        http_url=None,
        pdf_path=None,
        pdf_style=defaults.PDF_STYLE,
        report_tags=None,
        report_tags_all=None,
        resource_monitor=False,
        merge_scheduled_parts=False,
        browse=False,
        ui_port=None,
        web_server_startup_timeout=defaults.WEB_SERVER_TIMEOUT,
        test_filter=filtering.Filter(),
        test_sorter=ordering.NoopSorter(),
        test_lister=None,
        test_lister_output=None,
        verbose=False,
        debug=False,
        timeout=defaults.TESTPLAN_TIMEOUT,
        interactive_handler=TestRunnerIHandler,
        extra_deps=None,
        label=None,
        driver_info=False,
        collect_code_context=False,
        auto_part_runtime_limit=defaults.AUTO_PART_RUNTIME_LIMIT,
        plan_runtime_target=defaults.PLAN_RUNTIME_TARGET,
        **options,
    ):
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
                plan = cls(
                    name=name,
                    description=description,
                    parse_cmdline=parse_cmdline,
                    parser=parser,
                    interactive_port=interactive_port,
                    abort_signals=abort_signals,
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
                    json_path=json_path,
                    http_url=http_url,
                    pdf_path=pdf_path,
                    pdf_style=pdf_style,
                    report_tags=report_tags,
                    report_tags_all=report_tags_all,
                    resource_monitor=resource_monitor,
                    merge_scheduled_parts=merge_scheduled_parts,
                    browse=browse,
                    ui_port=ui_port,
                    web_server_startup_timeout=web_server_startup_timeout,
                    test_filter=test_filter,
                    test_sorter=test_sorter,
                    test_lister=test_lister,
                    test_lister_output=test_lister_output,
                    verbose=verbose,
                    debug=debug,
                    timeout=timeout,
                    interactive_handler=interactive_handler,
                    extra_deps=extra_deps,
                    label=label,
                    driver_info=driver_info,
                    collect_code_context=collect_code_context,
                    auto_part_runtime_limit=auto_part_runtime_limit,
                    plan_runtime_target=plan_runtime_target,
                    **options,
                )
                try:
                    returned = cls._prepare_plan(definition, plan)
                except Exception:
                    print("Exception in test_plan definition, aborting plan..")
                    plan.abort()
                    raise

                cls._do_listing(plan)

                plan_result = plan.run()
                plan_result.decorated_value = returned
                return plan_result

            return test_plan_inner_inner

        return test_plan_inner

    @classmethod
    def _prepare_plan(cls, definition, plan):
        if arity(definition) == 2:
            returned = definition(plan, plan.parser)
        else:
            returned = definition(plan)
        return returned

    @classmethod
    def _do_listing(cls, plan):
        lister: MetadataBasedLister = plan.cfg.test_lister
        if lister is not None and lister.metadata_based:
            output = lister.get_output(
                TestPlanMetadata(
                    plan.cfg.name,
                    plan.cfg.description,
                    plan.get_test_metadata(),
                )
            )
            if plan.cfg.test_lister_output:
                with open(plan.cfg.test_lister_output, "wt") as file:
                    file.write(output)
            else:
                TESTPLAN_LOGGER.user_info(output)


test_plan = Testplan.main_wrapper


def default_runpath_mock(entity):
    """To avoid runpath collision in testing"""
    prefix = "{}_".format(path.slugify(entity.uid()))
    if os.environ.get("TEST_ROOT_RUNPATH"):
        return tempfile.mkdtemp(
            prefix=prefix, dir=os.environ["TEST_ROOT_RUNPATH"]
        )
    else:
        return tempfile.mkdtemp(prefix=prefix)


class TestplanMock(Testplan):
    """
    A mock Testplan class for testing purpose. It is recommended to use
    mockplan fixture defined in conftest.py if you can. Only use this when
    necessary, e.g. you need to override default parameters.
    """

    def __init__(self, *args, **kwargs):
        # mock testplan could run in threads
        kwargs.setdefault("abort_signals", [])
        kwargs.setdefault("parse_cmdline", False)
        kwargs.setdefault("logger_level", logger.DEBUG)
        kwargs.setdefault("runpath", default_runpath_mock)

        super(TestplanMock, self).__init__(*args, **kwargs)
        self.runnable.disable_reset_report_uid()
