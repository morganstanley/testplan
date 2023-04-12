"""Generic application driver."""

import os
import uuid
import shutil
import warnings
import subprocess
import datetime
import platform
import socket
from typing import List, Union, Dict, Optional

try:
    from typing import Literal
except ImportError:
    from typing_extensions import Literal


from schema import Or

from testplan.common.config import ConfigOption
from testplan.common.utils.match import LogMatcher
from testplan.common.utils.path import StdFiles, makedirs, archive
from testplan.common.utils.context import is_context, expand, ContextValue
from testplan.common.utils.process import subprocess_popen, kill_process
from testplan.common.utils.timing import wait
from testplan.common.utils.documentation_helper import emphasized

from .base import Driver, DriverConfig, DriverMetadata

IS_WIN = platform.system() == "Windows"


class AppConfig(DriverConfig):
    """
    Configuration object for
    :py:class:`~testplan.testing.multitest.driver.app.App` resource.
    """

    @staticmethod
    def default_metadata_extractor(driver) -> DriverMetadata:
        return DriverMetadata(
            name=driver.name,
            driver_metadata={
                "class": driver.__class__.__name__,
                "outpath": driver.outpath,
                "errpath": driver.errpath,
            },
        )

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
            ConfigOption("sigint_timeout", default=5): int,
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
    :param env: Environmental variables to be made available to child process.
    :param binary_strategy: Whether to copy / link binary to runpath.
    :param logname: Base name of driver logfile under `app_path`, in which
        Testplan will look for `log_regexps` as driver start-up condition.
        Default to "stdout" (to match the output stream of binary).
    :param app_dir_name: Application directory name.
    :param working_dir: Application working directory. Default: runpath
    :param expected_retcode: the expected return code of the subprocess.
        Default value is None meaning it won't be checked. Set it to 0 to
        ennsure the driver is always gracefully shut down.
    :param sigint_timeout: number of seconds to wait between ``SIGINT`` and ``SIGKILL``

    Also inherits all
    :py:class:`~testplan.testing.multitest.driver.base.Driver` options.
    """

    CONFIG = AppConfig

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
        sigint_timeout: int = 5,
        **options,
    ) -> None:
        options.update(self.filter_locals(locals()))
        super(App, self).__init__(**options)
        self.proc = None
        self.std = None
        self.binary = None
        self._binpath: str = None
        self._etcpath: str = None
        self._retcode = None
        self._log_matcher = None

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

    @emphasized
    @property
    def cmd(self) -> str:
        """Command that starts the application."""
        args = self.cfg.args or []
        pre_args = self.cfg.pre_args or []
        cmd = []
        cmd.extend(pre_args)
        cmd.append(self.binary or self.cfg.binary)
        cmd.extend(args)
        cmd = [
            expand(arg, self.context, str) if is_context(arg) else arg
            for arg in cmd
        ]
        return cmd

    @emphasized
    @property
    def env(self) -> Dict[str, str]:
        """Environment variables."""
        if isinstance(self.cfg.env, dict):
            return {
                key: expand(val, self.context, str) if is_context(val) else val
                for key, val in self.cfg.env.items()
            }
        else:
            return None

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
            self._log_matcher = LogMatcher(self.logpath)
        return self._log_matcher

    def _prepare_binary(self, path: str) -> str:
        """prepare binary path"""
        return path

    @property
    def hostname(self) -> str:
        """
        :return: hostname where the ETSApp is running
        """
        return socket.gethostname()

    def pre_start(self) -> None:
        """
        Create mandatory directories and install files from given templates
        using the drivers context before starting the application binary.
        """
        super(App, self).pre_start()

        self._make_dirs()

        if self.cfg.path_cleanup is True:
            name = os.path.basename(self.cfg.binary)
        else:
            name = "{}-{}".format(
                os.path.basename(self.cfg.binary), uuid.uuid4()
            )

        self.binary = self._prepare_binary(self.cfg.binary)
        if os.path.isfile(self.binary):
            target = os.path.join(self._binpath, name)
            if self.cfg.binary_strategy == "copy":
                shutil.copyfile(self.binary, target)
                self.binary = target
            elif self.cfg.binary_strategy == "link" and not IS_WIN:
                os.symlink(os.path.abspath(self.binary), target)
                self.binary = target
            # else binary_strategy is noop then we don't do anything

        makedirs(self.app_path)
        self.std = StdFiles(self.app_path)

        if self.cfg.install_files:
            self._install_files()

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
                    "driver": self.uid(),
                    "cmd": cmd,
                    "runpath": self.runpath,
                    "out": self.std.out_path,
                    "err": self.std.err_path,
                },
            )
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
            if self.proc is not None:
                if self.proc.poll() is None:
                    kill_process(self.proc, self.cfg.sigint_timeout)
                assert self.proc.returncode is not None
                self._proc = None
            raise

    def started_check(self, timeout: Union[int, None] = None) -> Optional[int]:
        """
        Checks if app has started. Extracts logs and captured stdout/stderr.

        :param timeout: timeout in seconds
        """
        timeout = timeout if timeout is not None else self.cfg.timeout

        def ensure_app_running_while_extracting_values():
            proc_result = self.proc.poll()
            extract_values_result = self.extract_values()
            if proc_result is not None and not extract_values_result:
                raise RuntimeError(
                    f"{self} has unexpectedly stopped with: {proc_result}"
                )
            return extract_values_result

        wait(
            ensure_app_running_while_extracting_values,
            timeout,
            raise_on_timeout=True,
        )

    def stopping(self) -> None:
        """Stops the application binary process."""
        super(App, self).stopping()
        #
        if self.proc is None:
            return
        try:
            self._retcode = kill_process(self.proc, self.cfg.sigint_timeout)
        except Exception as exc:
            warnings.warn(f"On killing driver {self} process - {exc}")
            self._retcode = self.proc.poll() if self.proc else 0
        self.proc = None
        if self.std:
            self.std.close()
        self._log_matcher = None

        if (self.cfg.expected_retcode is not None) and (
            self.cfg.expected_retcode != self.retcode
        ):
            err_msg = (
                f"App driver error: {self},"
                f" expected return code is {self.cfg.expected_retcode},"
                f" but actual return code is {self.retcode}"
            )
            raise RuntimeError(err_msg)

    def _make_dirs(self) -> None:
        bin_dir = os.path.join(self.runpath, "bin")
        etc_dir = os.path.join(self.runpath, "etc")
        for directory in (bin_dir, etc_dir):
            makedirs(directory)
        self._binpath = bin_dir
        self._etcpath = etc_dir

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
            kill_process(self.proc, self.cfg.sigint_timeout)
        if self.std:
            self.std.close()
