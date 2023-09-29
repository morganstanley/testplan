"""Testplan base module."""
import argparse
import json
import os
import random
import signal
import sys
import tempfile
import traceback
import threading

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
from testplan.testing import filtering, ordering
from testplan.testing.listing import Lister, MetadataBasedLister
from testplan.testing.multitest.test_metadata import TestPlanMetadata


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
    :type name: ``str``
    :param description: Description of test plan.
    :type description: ``str``
    :param parse_cmdline: Parse command line arguments.
    :type parse_cmdline: ``bool``
    :param parser: Command line parser.
    :type parser: :py:class:`~testplan.parser.TestplanParser`
    :param interactive_port: Enable interactive execution mode on a port.
    :type interactive_port: ``int`` or ``NoneType``
    :param abort_signals: Signals to catch and trigger abort. By default,
        SIGINT and SIGTERM will trigger Testplan to abort.
    :type abort_signals: ``list`` of signals
    :param logger_level: Logger level for stdout.
    :type logger_level: ``int``
    :param: file_log_level: Logger level for file.
    :type file_log_level: ``int``
    :param runpath: Input runpath.
    :type runpath: ``str`` or ``callable``
    :param path_cleanup: Clean previous runpath entries.
    :type path_cleanup: ``bool``
    :param all_tasks_local: Schedule all tasks in local pool.
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
    :param json_path: JSON output path <PATH>/\*.json.
    :type json_path: ``str``
    :param http_url: HTTP url to post JSON report.
    :type http_url: ``str``
    :param pdf_path: PDF output path <PATH>/\*.pdf.
    :type pdf_path: ``str``
    :param pdf_style: PDF creation styling options.
    :type pdf_style:
        :py:class:`Style <testplan.report.testing.styles.Style>`
    :param report_tags: Matches tests marked with any of the given tags.
    :type report_tags: ``list``
    :param report_tags_all: Match tests marked with all of the given tags.
    :type report_tags_all: ``list``
    :param merge_scheduled_parts: Merge reports of scheduled MultiTest
        parts.
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
    :param test_lister_output: listing results goes to this file, if None goes to stdout
    :type test_lister: PathLike object
    :param verbose: Enable or disable verbose mode.
    :type verbose: ``bool``
    :param debug: Enable or disable debug mode.
    :type debug: ``bool``
    :param timeout: Timeout value in seconds to kill Testplan and all child
        processes, default to 14400s(4h), set to 0 to disable.
    :type timeout: ``int``
    :param interactive_handler: Handler for interactive mode execution.
    :type interactive_handler: Subclass of :py:class:
        `TestRunnerIHandler <testplan.runnable.interactive.TestRunnerIHandler>`
    :param extra_deps: Extra module dependencies for interactive reload, or
        paths of these modules.
    :type extra_deps: ``list`` of ``module`` or ``str``
    :param label: Label the test report with the given name, useful to
        categorize or classify similar reports .
    :type label: ``str`` or ``NoneType``
    """

    CONFIG = TestplanConfig

    # NOTE: if adding, deleting or modifying a constructor parameter here you
    # MUST also update the class docstring above and main_wrapper entry point
    # below with the same change.
    def __init__(
        self,
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
        auto_part_runtime_limit=defaults.AUTO_PART_RUNTIME_LIMIT,
        plan_runtime_target=defaults.PLAN_RUNTIME_TARGET,
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
            auto_part_runtime_limit=auto_part_runtime_limit,
            plan_runtime_target=plan_runtime_target,
            **options,
        )

        # By default, a LocalRunner is added to store and execute the tests.
        self._runnable.add_resource(LocalRunner(), uid="local_runner")

        # Stores independent environments.
        self._runnable.add_resource(Environments(), uid="environments")

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
