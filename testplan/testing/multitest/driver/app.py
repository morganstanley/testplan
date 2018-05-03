"""Generic application driver."""

import os
import uuid
import shutil
import warnings
import subprocess

from schema import Or

from testplan.common.config import ConfigOption
from testplan.common.utils.path import StdFiles, makedirs
from testplan.common.utils.context import is_context, expand
from testplan.common.utils.process import kill_process

from testplan.logger import TESTPLAN_LOGGER

from .base import Driver, DriverConfig


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
            'binary': str,
            ConfigOption('pre_args', default=None): Or(None, list),
            ConfigOption('args', default=None): Or(None, list),
            ConfigOption('shell', default=False): bool,
            ConfigOption('env', default=None): Or(None, dict),
            ConfigOption('binary_copy', default=False): bool,
            ConfigOption('app_dir_name', default=None): Or(None, str),
        }


class App(Driver):
    """
    Binary application driver.

    :param binary: Path the to application binary.
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
    :param binary_copy: Copy binary to a local binary path.
    :type binary_copy: ``bool``
    :param app_dir_name: Application directory name.
    :type app_dir_name: ``str``

    Also inherits all
    :py:class:`~testplan.testing.multitest.driver.base.DriverConfig`` options.
    """

    CONFIG = AppConfig

    def __init__(self, **options):
        super(App, self).__init__(**options)
        self.proc = None
        self.std = None
        self.binary = None
        self._binpath = None
        self._etcpath = None
        self._retcode = None

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
        cmd = [expand(arg, self.context, str) if is_context(arg) else arg
               for arg in cmd]
        return cmd

    @property
    def logpath(self):
        """Path for log regex matching."""
        if self.cfg.logfile:
            return os.path.join(self.app_path, self.cfg.logfile)
        return self.outpath

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

    def starting(self):
        """
        Create mandatory directories, install files from given templates
        using the drivers context and starts the application binary.
        """
        super(App, self).starting()
        self._make_dirs()
        if self.cfg.binary_copy:
            if self.cfg.path_cleanup is True:
                name = os.path.basename(self.cfg.binary)
            else:
                name = '{}-{}'.format(os.path.basename(self.cfg.binary),
                                      uuid.uuid4())

            target = os.path.join(self._binpath, name)
            shutil.copyfile(self.cfg.binary, target)
            self.binary = target
        else:
            self.binary = self.cfg.binary

        makedirs(self.app_path)
        self.std = StdFiles(self.app_path)

        if self.cfg.install_files:
            self._install_files()

        cmd = ' '.join(self.cmd) if self.cfg.shell else self.cmd
        try:
            self.logger.debug('{driver} driver command: {cmd},{linesep}'
                              '\trunpath: {runpath}{linesep}'
                              '\tout/err files {out} - {err}'.format(
                driver=self.uid(),
                cmd=cmd, runpath=self.runpath, linesep=os.linesep,
                out=self.std.out_path, err=self.std.err_path))
            self.proc = subprocess.Popen(cmd, shell=self.cfg.shell,
                stdout=self.std.out, stderr=self.std.err,
                cwd=self.runpath, env=self.cfg.env)
        except Exception:
            TESTPLAN_LOGGER.error(
                'Error while App[%s] driver executed command: %s',
                self.cfg.name, ' '.join(cmd))
            raise

    def stopping(self):
        """Stops the application binary process."""
        super(App, self).stopping()
        try:
            self._retcode = kill_process(self.proc)
        except Exception as exc:
            warnings.warn('On killing driver {} process - {}'.format(
                self.cfg.name, exc))
            self._retcode = self.proc.poll()
        self.proc = None
        if self.std:
            self.std.close()

    def _make_dirs(self):
        bin_dir = os.path.join(self.runpath, 'bin')
        etc_dir = os.path.join(self.runpath, 'etc')
        for directory in (bin_dir, etc_dir):
            makedirs(directory)
        self._binpath = bin_dir
        self._etcpath = etc_dir

    def _install_target(self):
        return self.etcpath

    def aborting(self):
        """Abort logic to force kill the child binary."""
        if self.proc:
            self.logger.debug('Killing process id {}'.format(self.proc.pid))
            kill_process(self.proc)
