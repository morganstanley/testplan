"""Driver base classes module."""

import os
import logging

from schema import Or

from testplan.common.config import ConfigOption
from testplan.common.entity import Resource, ResourceConfig, FailedAction
from testplan.common.utils.match import match_regexps_in_file
from testplan.common.utils.path import instantiate
from testplan.common.utils.timing import wait
from testplan.common.utils.documentation_helper import (
    get_metaclass_for_documentation,
)
from testplan.common.utils.documentation_helper import emphasized
from testplan.common.config.base import validate_func


def format_regexp_matches(name, regexps, unmatched):
    """
    Utility for formatting regexp match context,
    so it can rendered via TimeoutException
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
            ConfigOption("async_start", default=False): bool,
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

    :param name: Driver name. Also uid.
    :type name: ``str``
    :param install_files: list of files to be installed. This list may contain
        ``str`` or ``tuple``:

            - ``str``: Name of the file to be copied to path returned by
              ``_install_target`` method call
            - ``tuple``: A (source, destination) pair; source file
              will be copied to destination.

        Among other cases this is meant to be used with configuration files that
        may need to be templated and expanded using the runtime context, i.e:

        .. code-block:: xml

            <address>localhost:{{context['server'].port}}</address>

    :type install_files: ``List[Union[str, tuple]]``
    :param timeout: Timeout duration for status condition check.
    :type timeout: ``int``
    :param log_regexps: A list of regular expressions, any named groups matched
        in the logfile will be made available through ``extracts`` attribute.
        These will be start-up conditions.
    :type log_regexps: ``list`` of ``_sre.SRE_Pattern``
    :param stdout_regexps: Same with log_regexps but matching stdout file.
    :type stdout_regexps: ``list`` of ``_sre.SRE_Pattern``
    :param stderr_regexps: Same with log_regexps but matching stderr file.
    :type stderr_regexps: ``list`` of ``_sre.SRE_Pattern``
    :param file_logger: Send driver's log to a user specified file under its
        runpath. By default, logs go to console and top level "testplan.log".
        It is helpful when driver records too much details.
    :type file_logger: ``str`` or ``NoneType``
    :param async_start: Enable driver asynchronous start within an environment.
    :type async_start: ``bool``
    :param report_errors_from_logs: On startup/stop exception, report log
        lines from tail of stdout/stderr/logfile logs if enabled.
    :type report_errors_from_logs: ``bool``
    :param error_logs_max_lines: Number of lines to be reported if using
        `report_errors_from_logs` option.
    :type error_logs_max_lines: ``int``
    :param path_cleanup: Remove previous runpath created dirs/files.
    :type path_cleanup: ``bool``
    :param pre_start: Callable to execute before starting the driver.
    :type pre_start: ``callable`` taking a driver argument.
    :param post_start: Callable to execute after the driver is started.
    :type post_start: ``callable`` taking a driver argument.
    :param pre_stop: Callable to execute before stopping the driver.
    :type post_stop: ``callable`` taking a driver argument.
    :param pre_stop: Callable to execute after the driver is stopped.
    :type post_stop: ``callable`` taking a driver argument.

    Also inherits all
    :py:class:`~testplan.common.entity.base.Resource` options.
    """

    CONFIG = DriverConfig

    def __init__(
        self,
        name,
        install_files=None,
        timeout=300,
        log_regexps=None,
        stdout_regexps=None,
        stderr_regexps=None,
        file_logger=None,
        async_start=False,
        report_errors_from_logs=False,
        error_logs_max_lines=10,
        pre_start=None,
        post_start=None,
        pre_stop=None,
        post_stop=None,
        **options,
    ):

        options.update(self.filter_locals(locals()))
        if timeout is not None:
            options.setdefault("status_wait_timeout", timeout)
        super(Driver, self).__init__(**options)
        self.extracts = {}
        self._file_log_handler = None

    @emphasized
    @property
    def name(self):
        """Driver name."""
        return self.cfg.name

    @emphasized
    def uid(self):
        """Driver uid."""
        return self.cfg.name

    def pre_start(self):
        """Steps to be executed right before resource starts."""
        self.make_runpath_dirs()

    def started_check(self, timeout=None):
        """Driver started status condition check."""
        timeout = timeout if timeout is not None else self.cfg.timeout
        wait(
            lambda: self.extract_values(),
            timeout,
            raise_on_timeout=True,
        )

    def stopped_check(self, timeout=None):
        """Driver stopped status condition check."""

    def starting(self):
        """Trigger driver start."""
        self._setup_file_logger()

    def stopping(self):
        """Trigger driver stop."""
        self._close_file_logger()

    def _wait_started(self, timeout=None):
        self.started_check(timeout=timeout)
        super(Driver, self)._wait_started(timeout=timeout)

    def _wait_stopped(self, timeout=None):
        self.stopped_check(timeout=timeout)
        super(Driver, self)._wait_stopped(timeout=timeout)

    def aborting(self):
        """Trigger driver abort."""
        self._close_file_logger()

    def context_input(self):
        """Driver context information."""
        return {attr: getattr(self, attr) for attr in dir(self)}

    @property
    def logpath(self):
        """Path for log regex matching."""
        return self.outpath

    @property
    def outpath(self):
        """Path for stdout file regex matching."""
        return None

    @property
    def errpath(self):
        """Path for stderr file regex matching."""
        return None

    def extract_values(self):
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

    def _install_files(self):

        for install_file in self.cfg.install_files:
            if isinstance(install_file, str):
                if not os.path.isfile(install_file):
                    raise ValueError("{} is not a file".format(install_file))
                instantiate(
                    install_file, self.context_input(), self._install_target()
                )
            elif isinstance(install_file, tuple):
                if len(install_file) != 2:
                    raise ValueError(
                        "Expected the the source filepath, or a (source, "
                        "destination) pair; got {}".format(install_file)
                    )
                src, dst = install_file
                if not os.path.isabs(dst):
                    dst = os.path.join(self._install_target(), dst)
                instantiate(src, self.context_input(), dst)

    def _setup_file_logger(self):
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

    def _close_file_logger(self):
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

    def fetch_error_log(self):
        """
        Fetch error message from the log files of driver, at first we can
        try `self.errpath`, if it does not exist, try `self.logpath`.
        Typically, several lines from the tail of file will be selected.

        :return: Text from log file.
        :rtype: ``list`` of ``str``
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

    def __repr__(self):
        """String representation."""

        return f"{self.__class__.__name__} driver [{self.name}]"
