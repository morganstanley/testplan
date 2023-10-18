"""Driver base class module."""

import logging
import os
from dataclasses import dataclass, field
from enum import Enum
from typing import Any, Callable, Dict, List, Optional, Pattern, Tuple, Union

from schema import Or

from testplan.common.config import UNSET, UNSET_T, ConfigOption, validate_func
from testplan.common.entity import (
    ActionResult,
    FailedAction,
    Resource,
    ResourceConfig,
)
from testplan.common.utils.context import ContextValue, render
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
)


def format_regexp_matches(
    name: str, regexps: List[Pattern], unmatched: List
) -> str:
    """
    Utility for formatting regexp match context for rendering.

    :param name: name of regexp group
    :param regexps: list of compiled regexps
    :param unmatched: list of unmatched regexps
    :return: message to be used in exception raised or empty string
    """
    if unmatched:
        err = "{newline} {name} matched: {matched}".format(
            newline=os.linesep,
            name=name,
            matched=[
                "REGEX('{}')".format(e.pattern)
                for e in regexps
                if e not in unmatched
            ],
        )

        err += "{newline}Unmatched: {unmatched}".format(
            newline=os.linesep,
            unmatched=["REGEX('{}')".format(e.pattern) for e in unmatched],
        )
        return err
    return ""


class Direction(Enum):
    connecting = "connecting"
    listening = "listening"


@dataclass
class Connection:
    """
    Base class for connection information objects.

    Such objects ideally hold data with respect to the participants in the
     connection, the ports and hosts, or the protocol.
    """

    name: str
    protocol: str
    identifier: Union[int, str, ContextValue]
    direction: Direction

    def to_dict(self):
        return {
            "protocol": self.protocol,
            "identifier": self.identifier,
            "direction": self.direction,
        }


@dataclass
class DriverMetadata:
    """
    Base class for holding Driver metadata.

    :param name:
    :param driver_metadata:
    :param conn_info: list of connection info objects
    """

    name: str
    driver_metadata: Dict
    conn_info: List[Connection] = field(default_factory=list)

    def to_dict(self) -> Dict:
        """
        Returns the metadata of the driver except for the connections.
        """
        data = self.driver_metadata
        if self.conn_info:
            data["Connections"] = {
                conn.name: conn.to_dict() for conn in self.conn_info
            }
        return data


class DriverConfig(ResourceConfig):
    """
    Configuration object for
    :py:class:`~testplan.testing.multitest.driver.base.Driver` resource.
    """

    @staticmethod
    def default_metadata_extractor(driver) -> DriverMetadata:
        return DriverMetadata(
            name=driver.name,
            driver_metadata={"class": driver.__class__.__name__},
        )

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
            ConfigOption(
                "metadata_extractor", default=cls.default_metadata_extractor
            ): validate_func("driver"),
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
    :param metadata_extractor: callable for driver metadata extraction

    Also inherits all
    :py:class:`~testplan.common.entity.base.Resource` options.
    """

    CONFIG = DriverConfig

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
        metadata_extractor: Callable = None,
        **options,
    ):

        options.update(self.filter_locals(locals()))
        if timeout is not None:
            options.setdefault("status_wait_timeout", timeout)
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

    def starting(self) -> None:
        """Triggers driver start."""
        self._setup_file_logger()

    def stopping(self) -> None:
        """Triggers driver stop."""
        self._close_file_logger()

    def _wait_started(self, timeout: Optional[float] = None) -> None:
        sleeper = get_sleeper(
            interval=self.started_check_interval,
            timeout=timeout if timeout is not None else self.cfg.timeout,
            raise_timeout_with_msg=lambda: f"Timeout when starting {self}",
            timeout_info=True,
        )
        while next(sleeper):
            if self.started_check():
                break
        super(Driver, self)._wait_started(timeout=timeout)

    def _wait_stopped(self, timeout: Optional[float] = None) -> None:
        sleeper = get_sleeper(
            interval=self.stopped_check_interval,
            timeout=timeout if timeout is not None else self.cfg.timeout,
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
        log_unmatched = []
        stdout_unmatched = []
        stderr_unmatched = []
        result = True

        regex_sources = []
        if self.logpath and self.cfg.log_regexps:
            regex_sources.append(
                (self.logpath, self.cfg.log_regexps, log_unmatched)
            )
        if self.outpath and self.cfg.stdout_regexps:
            regex_sources.append(
                (self.outpath, self.cfg.stdout_regexps, stdout_unmatched)
            )
        if self.errpath and self.cfg.stderr_regexps:
            regex_sources.append(
                (self.errpath, self.cfg.stderr_regexps, stderr_unmatched)
            )

        for outfile, regexps, unmatched in regex_sources:
            file_result, file_extracts, file_unmatched = match_regexps_in_file(
                logpath=outfile, log_extracts=regexps
            )
            unmatched.extend(file_unmatched)
            for k, v in file_extracts.items():
                if isinstance(v, bytes):
                    self.extracts[k] = v.decode("utf-8")
                else:
                    self.extracts[k] = v
            result = result and file_result

        if log_unmatched or stdout_unmatched or stderr_unmatched:

            err = (
                "Timed out starting {}({}):" " unmatched log_regexps in {}."
            ).format(type(self).__name__, self.name, self.logpath)

            err += format_regexp_matches(
                name="log_regexps",
                regexps=self.cfg.log_regexps,
                unmatched=log_unmatched,
            )

            err += format_regexp_matches(
                name="stdout_regexps",
                regexps=self.cfg.stdout_regexps,
                unmatched=stdout_unmatched,
            )

            err += format_regexp_matches(
                name="stderr_regexps",
                regexps=self.cfg.stderr_regexps,
                unmatched=stderr_unmatched,
            )

            if self.extracts:
                err += "{newline}Matching groups:{newline}".format(
                    newline=os.linesep
                )
                err += os.linesep.join(
                    [
                        "\t{}: {}".format(key, value)
                        for key, value in self.extracts.items()
                    ]
                )
            return FailedAction(error_msg=err)
        return result

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

    def extract_driver_metadata(self) -> DriverMetadata:
        """
        Extracts driver metadata as described in the extractor function.

        :return: driver metadata
        """
        # pylint: disable=not-callable
        return self.cfg.metadata_extractor(self)
        # pylint: enable=not-callable

    def __str__(self):
        return f"{self.__class__.__name__}[{self.name}]"
