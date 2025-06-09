"""Driver base class module."""

import logging
import os
import time
from typing import Callable, Dict, List, Optional, Pattern, Tuple, Union

from schema import Or

from testplan.common.config import UNSET, UNSET_T, ConfigOption, validate_func
from testplan.common.entity import (
    ActionResult,
    FailedAction,
    Resource,
    ResourceConfig,
)
from testplan.common.utils.context import render
from testplan.common.utils.documentation_helper import (
    emphasized,
    get_metaclass_for_documentation,
)
from testplan.common.utils.match import match_regexps_in_file
from testplan.common.utils.path import instantiate
from testplan.common.utils.timing import (
    DEFAULT_INTERVAL,
    PollInterval,
    get_sleeper,
    wait,
    TimeoutException,
    TimeoutExceptionInfo,
)
from testplan.testing.multitest.driver.connection import (
    BaseConnectionInfo,
    BaseConnectionExtractor,
)


class DriverConfig(ResourceConfig):
    """
    Configuration object for
    :py:class:`~testplan.testing.multitest.driver.base.Driver` resource.
    """

    @classmethod
    def get_options(cls):
        """
        Schema for options validation and assignment of default values.
        """
        return {
            "name": str,
            ConfigOption("install_files", default=None): Or(None, list),
            ConfigOption("timeout", default=300): int,
            ConfigOption("log_regexps", default=None): Or(None, list),
            ConfigOption("stdout_regexps", default=None): Or(None, list),
            ConfigOption("stderr_regexps", default=None): Or(None, list),
            ConfigOption("file_logger", default=None): Or(None, str),
            ConfigOption("async_start", default=UNSET): Or(UNSET_T, bool),
            ConfigOption("report_errors_from_logs", default=False): bool,
            ConfigOption("error_logs_max_lines", default=10): int,
            ConfigOption("path_cleanup", default=True): bool,
            ConfigOption("pre_start", default=None): validate_func("driver"),
            ConfigOption("post_start", default=None): validate_func("driver"),
            ConfigOption("pre_stop", default=None): validate_func("driver"),
            ConfigOption("post_stop", default=None): validate_func("driver"),
        }


class Driver(Resource, metaclass=get_metaclass_for_documentation()):
    """
    Driver base class providing common functionality.

    {emphasized_members_docs}

    :param name: driver name also used as UID
    :param install_files: list of files to be installed
    :param timeout: status check timeout in seconds
    :param log_regexps: regexps to be matched in logfile
    :param stdout_regexps: regexps to be matched in stdout file
    :param stderr_regexps: regexps to be matched in stderr file
    :param file_logger: filepath for driver log, defaults to top level TP log
    :param async_start: whether to allow async start in environment
    :param report_errors_from_logs: whether to log the tail of
        stdout/stderr/logfile logs upon start/stop exception
    :param error_logs_max_lines: number of lines to be logged from the
        tail of stdout/stderr/logfile logs if `report_errors_from_logs` is True
    :param path_cleanup: whether to remove existing runpath elements
    :param pre_start: callable to execute before starting the driver
    :param post_start: callable to execute after the driver is started
    :param pre_stop: callable to execute before stopping the driver
    :param pre_stop: callable to execute after the driver is stopped

    Also inherits all
    :py:class:`~testplan.common.entity.base.Resource` options.
    """

    CONFIG = DriverConfig
    EXTRACTORS: List[BaseConnectionExtractor] = []

    def __init__(
        self,
        name: str,
        install_files: List[Union[str, Tuple]] = None,
        timeout: int = 300,
        log_regexps: List[Pattern] = None,
        stdout_regexps: List[Pattern] = None,
        stderr_regexps: List[Pattern] = None,
        file_logger: str = None,
        async_start: Union[UNSET_T, bool] = UNSET,
        report_errors_from_logs: bool = False,
        error_logs_max_lines: int = 10,
        pre_start: Callable = None,
        post_start: Callable = None,
        pre_stop: Callable = None,
        post_stop: Callable = None,
        **options,
    ):
        options.update(self.filter_locals(locals()))
        super(Driver, self).__init__(**options)
        self.extracts = {}
        self._file_log_handler = None

        # NOTE: We should get rid of `async_start` in the future,
        # NOTE: we still keep it now for compatibility.
        self._async_start_override: Optional[bool] = None

    @emphasized
    @property
    def name(self) -> str:
        """Driver name."""
        return self.cfg.name

    @emphasized
    def uid(self) -> str:
        """Driver uid."""
        return self.cfg.name

    @property
    def async_start(self) -> bool:
        """Overrides the default `async_start` value in config."""
        return (
            self._async_start_override
            if self._async_start_override is not None
            else self.cfg.async_start
        )

    @async_start.setter
    def async_start(self, async_start_override: bool):
        self._async_start_override = async_start_override

    def pre_start(self) -> None:
        """Steps to be executed right before resource starts."""
        self.make_runpath_dirs()

        if self.cfg.install_files:
            self.install_files()

    @property
    def started_check_interval(self) -> PollInterval:
        """
        Driver started check interval.
        In practice this value is lower-bounded by 0.1 seconds.
        """
        return DEFAULT_INTERVAL

    @property
    def stopped_check_interval(self) -> PollInterval:
        """Driver stopped check interval."""
        return DEFAULT_INTERVAL

    def wait(self, target_status, timeout=None):
        """
        Wait until objects status becomes target status.

        :param target_status: expected status
        :type target_status: ``str``
        :param timeout: timeout in seconds
        :type timeout: ``int`` or ``NoneType``
        """
        if target_status in self._wait_handlers:
            self._wait_handlers[target_status](timeout=timeout)
        else:
            timeout = (
                timeout
                if timeout is not None
                else self.cfg.status_wait_timeout
            )
            wait(lambda: self.status == target_status, timeout=timeout)

    @property
    def start_timeout(self) -> float:
        return self.cfg.timeout

    @property
    def stop_timeout(self) -> float:
        return self.cfg.timeout

    def started_check(self) -> ActionResult:
        """
        Predicate indicating whether driver has fully started.

        Default implementation tests whether certain pattern exists in driver
        loggings, always returns True if no pattern is required.
        """
        return self.extract_values()

    def stopped_check(self) -> ActionResult:
        """
        Predicate indicating whether driver has fully stopped.

        Default implementation immediately returns True.
        """
        return True

    def stopped_check_with_watch(self, watch) -> ActionResult:
        if time.time() >= watch.start_time + watch.total_wait:
            raise TimeoutException(
                f"Timeout when stopping {self}. "
                f"{TimeoutExceptionInfo(watch.start_time).msg()}"
            )

        if watch.should_check():
            return self.stopped_check()

        return False

    def starting(self) -> None:
        """Triggers driver start."""
        self._setup_file_logger()

    def stopping(self) -> None:
        """Triggers driver stop."""
        self._close_file_logger()

    def _wait_started(self, timeout: Optional[float] = None) -> None:
        sleeper = get_sleeper(
            interval=self.started_check_interval,
            timeout=timeout if timeout is not None else self.start_timeout,
        )

        info = TimeoutExceptionInfo(time.time())
        while next(sleeper):
            rc = self.started_check()
            if rc:
                break
        else:
            raise TimeoutException(
                f"Timeout when starting {self}. {info.msg()}\n\n{getattr(rc, 'error_msg', '')}"
            )

        super(Driver, self)._wait_started(timeout=timeout)

    def _wait_stopped(self, timeout: Optional[float] = None) -> None:
        sleeper = get_sleeper(
            interval=self.stopped_check_interval,
            timeout=timeout if timeout is not None else self.stop_timeout,
            raise_timeout_with_msg=lambda: f"Timeout when stopping {self}",
            timeout_info=True,
        )
        while next(sleeper):
            if self.stopped_check():
                break
        super(Driver, self)._wait_stopped(timeout=timeout)

    def aborting(self) -> None:
        """Triggers driver abort."""
        self._close_file_logger()

    @property
    def logpath(self):
        """Path for log regexp matching."""
        return self.outpath

    @property
    def outpath(self):
        """Path for stdout file regexp matching."""
        return None

    @property
    def errpath(self):
        """Path for stderr file regexp matching."""
        return None

    def extract_values(self) -> ActionResult:
        """Extract matching values from input regex configuration options."""
        rc = True
        err = f"{self} started_check failed, unmatched regexps:\n"

        for name, filepath, regexps in (
            ("log_regexps", self.logpath, self.cfg.log_regexps),
            ("stdout_regexps", self.outpath, self.cfg.stdout_regexps),
            ("stderr_regexps", self.errpath, self.cfg.stderr_regexps),
        ):
            if not filepath or not regexps:
                continue

            result, extracts, unmatched = match_regexps_in_file(
                filepath, regexps
            )
            rc = rc and result

            for k, v in extracts.items():
                if isinstance(v, bytes):
                    self.extracts[k] = v.decode("utf-8")
                else:
                    self.extracts[k] = v

            if unmatched:
                err += (
                    f"\tFile: {filepath}\n\tUnmatched {name}: {unmatched}\n\n"
                )
        if self.extracts:
            err += f"Extracted Values:\n"
            err += "\n".join(
                [f"\t{key}: {value}" for key, value in self.extracts.items()]
            )

        if not rc:
            return FailedAction(error_msg=err)
        return rc

    def _install_target(self):
        raise NotImplementedError()

    def install_files(self) -> None:
        """
        Installs the files specified in the install_files parameter at the install target.
        """
        context = self.context_input()
        for install_file in self.cfg.install_files:
            if isinstance(install_file, str):
                # may have jinja2/tempita template in file path
                install_file = render(install_file, context)
                if not os.path.isfile(install_file):
                    raise ValueError("{} is not a file".format(install_file))
                instantiate(install_file, context, self._install_target())
            elif isinstance(install_file, tuple):
                if len(install_file) != 2:
                    raise ValueError(
                        "Expected the the source filepath, or a (source, "
                        "destination) pair; got {}".format(install_file)
                    )
                src, dst = install_file
                # may have jinja2/tempita template in file path
                src = render(src, context)
                dst = render(dst, context)
                if not os.path.isabs(dst):
                    dst = os.path.join(self._install_target(), dst)
                instantiate(src, self.context_input(), dst)

    def _setup_file_logger(self) -> None:
        """
        Set up a logger to write to a given path at self.cfg.file_logger under
        driver's runpath.

        Logging to separate files should be used sparingly, for drivers that
        generate very large amounts of logs that are not suitable for including
        in the main console output even as a --debug option.

        When a file logger is finished with, _close_file_logger() should be
        called to close the opened file object and release the file handle.
        """
        if self._file_log_handler is not None:
            raise RuntimeError("{}: File logger already exists".format(self))

        # Note that in unit test driver's runpath might not be set
        if self.cfg.file_logger and self.runpath is not None:
            formatter = logging.Formatter(
                "%(asctime)s %(levelname)s %(message)s"
            )
            self._file_log_handler = logging.FileHandler(
                os.path.join(self.runpath, self.cfg.file_logger)
            )
            self._file_log_handler.setFormatter(formatter)
            self.logger.addHandler(self._file_log_handler)
            self.logger.propagate = False  # No console logs

    def _close_file_logger(self) -> None:
        """
        Closes a handler previously opened by _setup_file_logger() and removes
        the file handler from self.logger. This should be called when the file
        logger is done with to avoid leaking file handles - typically this
        should be called from stopping().
        """
        if self._file_log_handler is not None:
            self._file_log_handler.flush()
            self._file_log_handler.close()
            self.logger.removeHandler(self._file_log_handler)
            self._file_log_handler = None
            self.logger.propagate = True

    def fetch_error_log(self) -> List[str]:
        """
        Fetch error message from the log files of driver, at first we can
        try `self.errpath`, if it does not exist, try `self.logpath`.
        Typically, several lines from the tail of file will be selected.

        :return: text from log file
        """
        content = []

        def get_lines_at_tail(log_file, max_count):
            """Fetch last n lines from a big file."""
            if not os.path.exists(log_file):
                return []

            file_size = os.path.getsize(log_file)
            # Assume that in average a line has 512 characters at most
            block_size = max_count * 512 if max_count > 0 else file_size

            with open(log_file, "r") as file_handle:
                if file_size > block_size > 0:
                    max_seek_point = file_size // block_size
                    file_handle.seek((max_seek_point - 1) * block_size)
                elif file_size:
                    file_handle.seek(0, os.SEEK_SET)
                lines = file_handle.read().splitlines()
                while lines and not lines[-1]:
                    lines.pop()
                return lines[-max_count:] if max_count > 0 else lines

        logging_paths = {self.errpath, self.outpath, self.logpath}
        if self.cfg.file_logger:
            file_log_path = os.path.join(self.runpath, self.cfg.file_logger)
            if file_log_path not in logging_paths:
                logging_paths.add(file_log_path)

        for path in logging_paths:
            lines = (
                get_lines_at_tail(path, self.cfg.error_logs_max_lines)
                if path
                else []
            )
            if lines:
                if content:
                    content.append("")
                content.append("Information from log file: {}".format(path))
                content.extend(["  {}".format(line) for line in lines])

        return content

    def get_connections(self) -> List[BaseConnectionInfo]:
        connections = []
        for extractor in self.EXTRACTORS:
            connections.extend(extractor.extract_connection(self))
        return connections

    def __str__(self):
        return f"{self.__class__.__name__}[{self.name}]"
