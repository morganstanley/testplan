"""Generic application driver."""

import os
import uuid
import shutil
import warnings
import subprocess
import datetime
import platform
import socket

from schema import Or

from testplan.common.config import ConfigOption
from testplan.common.utils.match import LogMatcher
from testplan.common.utils.path import StdFiles, makedirs, archive
from testplan.common.utils.context import is_context, expand
from testplan.common.utils.process import subprocess_popen, kill_process
from testplan.common.utils.timing import wait

from .base import Driver, DriverConfig

IS_WIN = platform.system() == "Windows"


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
        }


class App(Driver):
    """
    Binary application driver.

    :param name: Driver name. Also uid.
    :type name: ``str``
    :param binary: Path to the application binary.
    :type binary: ``str``
    :param pre_args: Arguments to be prepended to binary command. An argument
        can be a :py:class:`~testplan.common.utils.context.ContextValue`
        and will be expanded on runtime.
    :type pre_args: ``list`` or ``str``
    :param args: Arguments to be appended to binary command. An argument
        can be a :py:class:`~testplan.common.utils.context.ContextValue`
        and will be expanded on runtime.
    :type args: ``list`` of ``str``
    :param shell: Invoke shell for command execution.
    :type shell: ``bool``
    :param env: Environmental variables to be made available to child process.
    :type env: ``dict``
    :param binary_strategy: Whether to copy / link binary to runpath.
    :type binary_strategy: one of ("copy", "link", "noop")
    :param logname: Base name of driver logfile under `app_path`, in which
        Testplan will look for `log_regexps` as driver start-up condition.
        Default to "stdout" (to match the output stream of binary).
    :type logname: ``str``
    :param app_dir_name: Application directory name.
    :type app_dir_name: ``str`` or ``NoneType``
    :param working_dir: Application working directory. Default: runpath
    :type working_dir: ``str`` or ``NoneType``
    :param expected_retcode: the expected return code of the subprocess.
        Default value is None meaning it won't be checked. Set it to 0 to
        ennsure the driver is always gracefully shut down.
    :type expected_retcode: ``Optional[int]``

    Also inherits all
    :py:class:`~testplan.testing.multitest.driver.base.Driver` options.
    """

    CONFIG = AppConfig

    def __init__(
        self,
        name,
        binary,
        pre_args=None,
        args=None,
        shell=False,
        env=None,
        binary_strategy="link",
        logname=None,
        app_dir_name=None,
        working_dir=None,
        expected_retcode=None,
        **options,
    ):
        options.update(self.filter_locals(locals()))
        super(App, self).__init__(**options)
        self.proc = None
        self.std = None
        self.binary = None
        self._binpath = None
        self._etcpath = None
        self._retcode = None
        self._log_matcher = None

    @property
    def pid(self):
        """
        Return pid of the child process if available, ``None`` otherwise.

        :rtype: ``int`` or ``NoneType``
        """
        if self.proc:
            return self.proc.pid
        else:
            return None

    @property
    def retcode(self):
        """
        Return return code of the app process or ``None``.

        :rtype: ``int`` or ``NoneType``
        """
        if self._retcode is None:
            if self.proc:
                self._retcode = self.proc.poll()
        return self._retcode

    @property
    def cmd(self):
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

    @property
    def env(self):
        """Environment variables."""
        if isinstance(self.cfg.env, dict):
            return {
                key: expand(val, self.context, str) if is_context(val) else val
                for key, val in self.cfg.env.items()
            }
        else:
            return None

    @property
    def logname(self):
        """Configured logname."""
        return self.cfg.logname

    @property
    def logpath(self):
        """Path for log regex matching."""
        return (
            os.path.join(self.app_path, self.logname)
            if self.logname
            else self.outpath
        )

    @property
    def outpath(self):
        """Path for stdout file regex matching."""
        return self.std.out_path

    @property
    def errpath(self):
        """Path for stderr file regex matching."""
        return self.std.err_path

    @property
    def app_path(self):
        """Application directory path."""
        if self.cfg.app_dir_name:
            return os.path.join(self.runpath, self.cfg.app_dir_name)
        return self.runpath

    @property
    def binpath(self):
        """'bin' directory under runpath."""
        return self._binpath

    @property
    def etcpath(self):
        """'etc' directory under runpath."""
        return self._etcpath

    @property
    def log_matcher(self):
        """
        Create if not exist and return the LogMatcher object that reads the
        log / stdout of the driver.

        :return: LogMatcher instance
        :rtype: ``LogMatcher``
        """
        if not self._log_matcher:
            self._log_matcher = LogMatcher(self.logpath)
        return self._log_matcher

    def _prepare_binary(self, path):
        """prepare binary path"""
        return path

    @property
    def hostname(self):
        """
        :return: hostname where the ETSApp is running
        :rtype: ``str``
        """
        return socket.gethostname()

    def pre_start(self):
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

    def starting(self):
        """Starts the application binary."""
        super(App, self).starting()

        cmd = " ".join(self.cmd) if self.cfg.shell else self.cmd
        cwd = self.cfg.working_dir or self.runpath
        try:
            self.logger.debug(
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
                "Error while App[%s] driver executed command: %s",
                self.cfg.name,
                cmd if self.cfg.shell else " ".join(cmd),
            )
            if self.proc is not None:
                if self.proc.poll() is None:
                    kill_process(self.proc)
                assert self.proc.returncode is not None
                self._proc = None
            raise

    def started_check(self, timeout=None):
        def ensure_app_running_while_extracting_values():
            proc_result = self.proc.poll()
            extract_values_result = self.extract_values()
            if proc_result is not None and not extract_values_result:
                raise RuntimeError(
                    f"App {self.name} has unexpectedly stopped with: {proc_result}"
                )
            return extract_values_result

        wait(
            ensure_app_running_while_extracting_values,
            timeout or self.cfg.timeout,
            raise_on_timeout=True,
        )

    def stopping(self):
        """Stops the application binary process."""
        super(App, self).stopping()
        #
        if self.proc is None:
            return
        try:
            self._retcode = kill_process(self.proc)
        except Exception as exc:
            warnings.warn(
                "On killing driver {} process - {}".format(self.cfg.name, exc)
            )
            self._retcode = self.proc.poll() if self.proc else 0
        self.proc = None
        if self.std:
            self.std.close()
        self._log_matcher = None

        if (self.cfg.expected_retcode is not None) and (
            self.cfg.expected_retcode != self.retcode
        ):
            err_msg = (
                f"App drier error: {self.name},"
                f" expected return cde is {self.cfg.expected_retcode},"
                f" but actual return code is {self.retcode}"
            )
            raise RuntimeError(err_msg)

    def _make_dirs(self):
        bin_dir = os.path.join(self.runpath, "bin")
        etc_dir = os.path.join(self.runpath, "etc")
        for directory in (bin_dir, etc_dir):
            makedirs(directory)
        self._binpath = bin_dir
        self._etcpath = etc_dir

    def _install_target(self):
        return self.etcpath

    def restart(self, clean=True):
        """
        Stop the driver, archive the app_dir or rename std/log, and then restart
        the driver.

        :param clean: if set to ``True``, perform a 'clean' restart where
            all persistence is deleted, else a normal restart.
        :type clean: ``bool``

        """
        self.stop()
        self.wait(self.status.STOPPED)
        if clean:
            self._move_app_path()
        else:
            self._move_std_and_logs()

        # we don't want to cleanup runpath during restart
        path_cleanup = self.cfg.path_cleanup
        self.cfg._options["path_cleanup"] = False
        self.start()
        self.wait(self.status.STARTED)
        self.cfg._options["path_cleanup"] = path_cleanup

    def _move_app_path(self):
        """
        Move app_path directory to an archive location
        """
        snapshot_path = self.app_path + datetime.datetime.now().strftime(
            "_%Y%m%d_%H%M%S"
        )

        shutil.move(self.app_path, snapshot_path)
        os.makedirs(self.app_path)

    def _move_std_and_logs(self):
        """
        Rename std and log files
        """
        timestamp = datetime.datetime.now().strftime("_%Y%m%d_%H%M%S")

        for file in (self.outpath, self.errpath, self.logpath):
            if os.path.isfile(file):
                archive(file, timestamp)

    def aborting(self):
        """Abort logic to force kill the child binary."""
        if self.proc:
            self.logger.debug("Killing process id {}".format(self.proc.pid))
            kill_process(self.proc)
        if self.std:
            self.std.close()
