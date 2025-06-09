"""Generic application driver."""

import datetime
import os
import platform
import shutil
import signal
import socket
import subprocess
import time
import uuid
import warnings
from typing import Dict, List, Optional, Union

try:
    from typing import Literal
except ImportError:
    from typing_extensions import Literal

import psutil
from schema import Or, Use

from testplan.common.config import ConfigOption
from testplan.common.entity import ActionResult
from testplan.common.utils.context import (
    ContextValue,
    expand,
    is_context,
    render,
)
from testplan.common.utils.documentation_helper import emphasized
from testplan.common.utils.match import LogMatcher
from testplan.common.utils.path import StdFiles, archive, makedirs
from testplan.common.utils.process import (
    kill_process,
    subprocess_popen,
    kill_proc_and_child_procs,
)
from testplan.common.utils.timing import TimeoutException, TimeoutExceptionInfo

from testplan.testing.multitest.driver.base import Driver, DriverConfig
from testplan.testing.multitest.driver.connection import (
    SubprocessFileConnectionExtractor,
    SubprocessPortConnectionExtractor,
)

IS_WIN = platform.system() == "Windows"


class OrphanedProcessException(Exception):
    """
    Exception raised when there are orphaned processes after stopping the
    driver.
    """

    def __init__(self, driver, procs):
        self.driver = driver
        self.procs = procs
        super().__init__(f"Orphaned processes detected: {procs} for {driver}")


class AppConfig(DriverConfig):
    """
    Configuration object for
    :py:class:`~testplan.testing.multitest.driver.app.App` resource.
    """

    @classmethod
    def get_options(cls):
        """
        Schema for options validation and assignment of default values.
        """
        return {
            "binary": str,
            ConfigOption("pre_args", default=None): Or(None, list),
            ConfigOption("args", default=None): Or(None, list),
            ConfigOption("shell", default=False): bool,
            ConfigOption("env", default=None): Or(None, dict),
            ConfigOption("binary_strategy", default="link"): lambda s: s
            in ("copy", "link", "noop"),
            ConfigOption("logname", default=None): Or(None, str),
            ConfigOption("app_dir_name", default=None): Or(None, str),
            ConfigOption("working_dir", default=None): Or(None, str),
            ConfigOption("expected_retcode", default=None): int,
            ConfigOption("stop_signal", default=None): Or(
                None, signal.Signals
            ),
            ConfigOption("stop_timeout", default=5): Use(float),
            ConfigOption("binary_log", default=False): bool,
        }


ArgsType = Union[List[Union[str, ContextValue]], str, ContextValue]


class App(Driver):
    """
    Binary application driver.

    {emphasized_members_docs}

    :param name: Driver name. Also uid.
    :param binary: Path to the application binary.
    :param pre_args: Arguments to be prepended to binary command. An argument
        can be a :py:class:`~testplan.common.utils.context.ContextValue`
        and will be expanded on runtime.
    :param args: Arguments to be appended to binary command. An argument
        can be a :py:class:`~testplan.common.utils.context.ContextValue`
        and will be expanded on runtime.
    :param shell: Invoke shell for command execution.
    :param env: Environmental variables to be made available to child process;
        context value (when referring to other driver) and jinja2 template (when
        referring to self) will be resolved.
    :param binary_strategy: Whether to copy / link binary to runpath.
    :param logname: Base name of driver logfile under `app_path`, in which
        Testplan will look for `log_regexps` as driver start-up condition.
        Default to "stdout" (to match the output stream of binary).
    :param app_dir_name: Application directory name.
    :param working_dir: Application working directory. Default: runpath
    :param expected_retcode: the expected return code of the subprocess.
        Default value is None meaning it won't be checked. Set it to 0 to
        ennsure the driver is always gracefully shut down.
    :param stop_signal: Shutdown signal to be sent to subprocess.
    :param stop_timeout: Timeout for graceful shutdown (in seconds).
    :param binary_log: if `True` the log_matcher will handle the logfile as binary,
        and need to use binary regexps. Default value is `False`.

    Also inherits all
    :py:class:`~testplan.testing.multitest.driver.base.Driver` options.
    """

    CONFIG = AppConfig
    EXTRACTORS = [
        SubprocessFileConnectionExtractor(),
        SubprocessPortConnectionExtractor(),
    ]

    def __init__(
        self,
        name: str,
        binary: str,
        pre_args: ArgsType = None,
        args: ArgsType = None,
        shell: bool = False,
        env: Dict[str, str] = None,
        binary_strategy: Literal["copy", "link", "noop"] = "link",
        logname: str = None,
        app_dir_name: str = None,
        working_dir: str = None,
        expected_retcode: int = None,
        stop_signal: Optional[signal.Signals] = None,
        stop_timeout: float = 5,
        binary_log: bool = False,
        **options,
    ) -> None:
        options.update(self.filter_locals(locals()))
        # ``sigint_timeout`` is deprecated
        if "sigint_timeout" in options:
            options["stop_timeout"] = options.pop("sigint_timeout")
            warnings.warn(
                "``sigint_timeout`` argument is deprecated, "
                "please use ``stop_timeout`` instead.",
                DeprecationWarning,
            )
        super(App, self).__init__(**options)
        self.proc = None
        self.std = None
        self._binary = None
        self._binpath: str = None
        self._etcpath: str = None
        self._retcode = None
        self._log_matcher = None
        self._resolved_bin = None
        self._env = None

        self._alive_child_procs = []  # for orphaned procs elimination

    @emphasized
    @property
    def pid(self) -> Optional[int]:
        """
        Return pid of the child process if available, ``None`` otherwise.
        """
        if self.proc:
            return self.proc.pid
        else:
            return None

    @property
    def retcode(self) -> Optional[int]:
        """
        Return return code of the app process or ``None``.
        """
        if self._retcode is None:
            if self.proc:
                self._retcode = self.proc.poll()
        return self._retcode

    @property
    def alive_child_procs(self) -> List[psutil.Process]:
        _, self._alive_child_procs = psutil.wait_procs(
            self._alive_child_procs, timeout=0
        )
        return self._alive_child_procs

    @emphasized
    @property
    def cmd(self) -> str:
        """Command that starts the application."""
        args = self.cfg.args or []
        pre_args = self.cfg.pre_args or []
        cmd = []
        cmd.extend(pre_args)
        cmd.append(self.binary)
        cmd.extend(args)
        cmd = [
            expand(arg, self.context, str) if is_context(arg) else arg
            for arg in cmd
        ]
        return cmd

    @emphasized
    @property
    def env(self) -> Optional[Dict[str, str]]:
        """Environment variables."""

        if self._env:
            return self._env

        if isinstance(self.cfg.env, dict):
            ctx = self.context_input(exclude=["env"])
            self._env = {
                key: expand(val, self.context, str)
                if is_context(val)
                # allowing None val for child class use case
                else (render(val, ctx) if val is not None else None)
                for key, val in self.cfg.env.items()
            }

        return self._env

    @emphasized
    @property
    def logname(self) -> str:
        """Configured logname."""
        return self.cfg.logname

    @emphasized
    @property
    def logpath(self) -> str:
        """Path for log regex matching."""
        return (
            os.path.join(self.app_path, self.logname)
            if self.logname
            else self.outpath
        )

    @emphasized
    @property
    def outpath(self) -> str:
        """Path for stdout file regex matching."""
        return self.std.out_path

    @emphasized
    @property
    def errpath(self) -> str:
        """Path for stderr file regex matching."""
        return self.std.err_path

    @emphasized
    @property
    def app_path(self) -> str:
        """Application directory path."""
        if self.cfg.app_dir_name:
            return os.path.join(self.runpath, self.cfg.app_dir_name)
        return self.runpath

    @emphasized
    @property
    def binpath(self) -> str:
        """'bin' directory under runpath."""
        return self._binpath

    @emphasized
    @property
    def binary(self) -> str:
        """The actual binary to execute, might be copied/linked to runpath"""

        if self._binary:
            return self._binary

        if os.path.isfile(self.resolved_bin):
            if self.cfg.path_cleanup is True:
                name = os.path.basename(self.cfg.binary)
            else:
                name = "{}-{}".format(
                    os.path.basename(self.cfg.binary), uuid.uuid4()
                )
            target = os.path.join(self.binpath, name)

            if self.cfg.binary_strategy == "copy":
                shutil.copyfile(self.resolved_bin, target)
                shutil.copymode(self.resolved_bin, target)
                self._binary = target
            elif self.cfg.binary_strategy == "link" and not IS_WIN:
                os.symlink(os.path.abspath(self.resolved_bin), target)
                self._binary = target
            # else binary_strategy is noop then we don't do anything
            else:
                self._binary = self.resolved_bin
        else:
            self._binary = self.resolved_bin

        return self._binary

    @emphasized
    @property
    def etcpath(self) -> str:
        """'etc' directory under runpath."""
        return self._etcpath

    @property
    def log_matcher(self) -> LogMatcher:
        """
        Create if not exist and return the LogMatcher object that reads the
        log / stdout of the driver.

        :return: LogMatcher instance
        """
        if not self._log_matcher:
            self._log_matcher = LogMatcher(self.logpath, self.cfg.binary_log)
        return self._log_matcher

    @property
    def resolved_bin(self) -> str:
        """Resolved binary path from self.cfg.binary"""
        if not self._resolved_bin:
            self._resolved_bin = self._prepare_binary()

        return self._resolved_bin

    def _prepare_binary(self) -> str:
        """prepare binary path, override for more sophisticated binary discover"""
        return self.cfg.binary

    @property
    def hostname(self) -> str:
        """
        :return: hostname where the ETSApp is running
        """
        return socket.gethostname()

    def starting(self) -> None:
        """Starts the application binary."""
        super(App, self).starting()

        cmd = " ".join(self.cmd) if self.cfg.shell else self.cmd
        cwd = self.cfg.working_dir or self.runpath
        try:
            self.logger.info(
                "%(driver)s driver command: %(cmd)s\n"
                "\tRunpath: %(runpath)s\n"
                "\tOut file: %(out)s\n"
                "\tErr file: %(err)s\n",
                {
                    "driver": self,
                    "cmd": cmd,
                    "runpath": self.runpath,
                    "out": self.std.out_path,
                    "err": self.std.err_path,
                },
            )
            self._retcode = None
            self.proc = subprocess_popen(
                cmd,
                shell=self.cfg.shell,
                stdin=subprocess.PIPE,
                stdout=self.std.out,
                stderr=self.std.err,
                cwd=cwd,
                env=self.env,
            )
        except Exception:
            self.logger.error(
                "Error while %s driver executed command: %s",
                self,
                cmd if self.cfg.shell else " ".join(cmd),
            )
            self.aborting()
            raise

    def started_check(self) -> ActionResult:
        """
        Predicate indicating whether a binary in a subprocess has started.
        Tests whether the return code is zero if the underlying binary has
        finished execution, otherwise tests if user-specified pattern exists in
        driver logs.
        """
        proc_result = self.proc.poll()
        extract_values_result = self.extract_values()
        if proc_result is not None and not extract_values_result:
            raise RuntimeError(
                f"{self} has unexpectedly stopped with: {proc_result}"
            )
        return extract_values_result

    @property
    def stop_timeout(self) -> float:
        return self.cfg.stop_timeout

    def stopping(self) -> None:
        """Stops the application binary process."""
        if self.proc is not None and self.retcode is None:
            # take a snapshot of all child procs
            # so that we can check if they all terminate later
            self._alive_child_procs = psutil.Process(self.pid).children(
                recursive=True
            )

            if self.cfg.stop_signal is None:
                self.proc.terminate()
            else:
                self.proc.send_signal(self.cfg.stop_signal)
        super().stopping()

    def stopped_check(self) -> ActionResult:
        if self.proc is None:
            return True

        if self.retcode is None:
            return False

        if self.alive_child_procs:
            raise OrphanedProcessException(self, self._alive_child_procs)

        return True

    def stopped_check_with_watch(self, watch) -> ActionResult:
        def log_fn(exc):
            self.logger.warning("While killing driver %s: %s", self, exc)

        if time.time() >= watch.start_time + watch.total_wait:
            # not raising a timeout here
            self.logger.warning(
                "%s still alive after %d seconds, killing",
                self,
                self.stop_timeout,
            )
            kill_proc_and_child_procs(
                self.proc, self.alive_child_procs, log_fn
            )

        if watch.should_check():
            try:
                return self.stopped_check()
            except OrphanedProcessException as exc:
                self.logger.warning(exc)
                kill_proc_and_child_procs(
                    self.proc, self.alive_child_procs, log_fn
                )
                return True

        return False

    def _wait_stopped(self, timeout: Optional[float] = None) -> None:
        # for App driver and its inheritance, always force stop

        def log_fn(exc):
            self.logger.warning("While killing driver %s: %s", self, exc)

        try:
            super()._wait_stopped(timeout)
        except TimeoutException:
            self.logger.warning(
                "%s still alive after %d seconds, killing",
                self,
                self.stop_timeout,
            )
            kill_proc_and_child_procs(
                self.proc, self.alive_child_procs, log_fn
            )
            self._mark_stopped()
        except OrphanedProcessException as exc:
            self.logger.warning(exc)
            kill_proc_and_child_procs(
                self.proc, self.alive_child_procs, log_fn
            )
            self._mark_stopped()

        # other exceptions gets propagated

    def post_stop(self):
        rc = self.retcode
        self.proc = None
        if self.std:
            self.std.close()

        # reset env, binary etc. as they need re-eval in case of restart
        self._env = None
        self._binary = None
        self._log_matcher = None

        if (self.cfg.expected_retcode is not None) and (
            self.cfg.expected_retcode != rc
        ):
            err_msg = (
                f"App driver error: {self},"
                f" expected return code is {self.cfg.expected_retcode},"
                f" but actual return code is {rc}"
            )
            raise RuntimeError(err_msg)

    def make_runpath_dirs(self) -> None:
        """
        Create mandatory directories and install files from given templates
        using the drivers context before starting the application binary.
        """
        super(App, self).make_runpath_dirs()

        bin_dir = os.path.join(self.runpath, "bin")
        etc_dir = os.path.join(self.runpath, "etc")
        for directory in (bin_dir, etc_dir, self.app_path):
            makedirs(directory)
        self._binpath = bin_dir
        self._etcpath = etc_dir
        self.std = StdFiles(self.app_path)

    def _install_target(self) -> str:
        return self.etcpath

    def restart(self, clean: bool = True) -> None:
        """
        Stop the driver, archive the app_dir or rename std/log, and then restart
        the driver.

        :param clean: if set to ``True``, perform a 'clean' restart where
            all persistence is deleted, else a normal restart.

        """
        self.stop()
        if self.async_start:
            self.wait(self.status.STOPPED)

        if clean:
            self._move_app_path()
        else:
            self._move_std_and_logs()

        # we don't want to cleanup runpath during restart
        path_cleanup = self.cfg.path_cleanup
        self.cfg._options["path_cleanup"] = False

        self.start()
        if self.async_start:
            self.wait(self.status.STARTED)

        self.cfg._options["path_cleanup"] = path_cleanup

    def _move_app_path(self) -> None:
        """
        Move app_path directory to an archive location
        """
        snapshot_path = self.app_path + datetime.datetime.now().strftime(
            "_%Y%m%d_%H%M%S"
        )

        shutil.move(self.app_path, snapshot_path)
        os.makedirs(self.app_path)

    def _move_std_and_logs(self) -> None:
        """
        Rename std and log files
        """
        timestamp = datetime.datetime.now().strftime("_%Y%m%d_%H%M%S")

        for file in (self.outpath, self.errpath, self.logpath):
            if os.path.isfile(file):
                archive(file, timestamp)

    def aborting(self) -> None:
        """Abort logic to force kill the child binary."""
        if self.proc:
            self.logger.info(
                "Killing process id %s of %s", self.proc.pid, self
            )
            kill_process(self.proc, self.stop_timeout, self.cfg.stop_signal)
            self.proc = None
        if self.std:
            self.std.close()
