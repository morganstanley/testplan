"""Driver base classes module."""

import os
import logging

from schema import Or

from testplan.common.config import ConfigOption
from testplan.common.entity import Resource, ResourceConfig, FailedAction
from testplan.common.utils.match import match_regexps_in_file
from testplan.common.utils.path import instantiate
from testplan.common.utils.timing import wait


def format_regexp_matches(name, regexps, unmatched):
    """
    Utility for formatting regexp match context,
    so it can rendered via TimeoutException
    """
    if unmatched:
        err = '{newline} {name} matched: {matched}'.format(
            newline=os.linesep,
            name=name,
            matched=[
                "REGEX('{}')".format(e.pattern)
                for e in regexps
                if e not in unmatched
            ])

        err += '{newline}Unmatched: {unmatched}'.format(
            newline=os.linesep,
            unmatched=[
                "REGEX('{}')".format(e.pattern)
                for e in unmatched
            ]
        )
        return err
    return ''


class DriverConfig(ResourceConfig):
    """
    Configuration object for
    :py:class:`~testplan.testing.multitest.driver.base.Driver` resource.
    """

    def configuration_schema(self):
        """
        Schema for options validation and assignment of default values.
        """
        overrides = {'name': str,
                     ConfigOption('install_files', default=None):
                         Or(None, list),
                     ConfigOption('timeout', default=5): int,
                     ConfigOption('logfile', default=None):
                         Or(None, str),
                     ConfigOption('log_regexps', default=None):
                         Or(None, list),
                     ConfigOption('stdout_regexps', default=None):
                         Or(None, list),
                     ConfigOption('stderr_regexps', default=None):
                         Or(None, list),
                     ConfigOption('async_start', default=False): bool
                     }
        return self.inherit_schema(overrides, super(DriverConfig, self))


class Driver(Resource):
    """
    Driver base class providing common functionality.

    :param name: Driver name. Also uid.
    :type name: ``str``
    :param install_files: List of filepaths, those files will be instantiated
      and placed under path returned by ``_install_target`` method call. Among
      other cases this is meant to be used with configuration files that may
      need to be templated and expanded using the runtime context, i.e:

      .. code-block:: xml

        <address>localhost:{{context['server'].port}}</address>

    :type install_files: ``list`` of ``str``
    :param timeout: Timeout duration for status condition check.
    :type timeout: ``int``
    :param logfile: Driver logfile path.
    :type logfile: ``str``
    :param log_regexps: A list of regular expressions, any named groups matched
      in the logfile will be made available through ``extracts`` attribute.
      These will be start-up conditions.
    :type log_regexps: ``list`` of ``_sre.SRE_Pattern``
    :param stdout_regexps: Same with log_regexps but matching stdout file.
    :type stdout_regexps: ``list`` of ``_sre.SRE_Pattern``
    :param stderr_regexps: Same with log_regexps but matching stderr file.
    :type stderr_regexps: ``list`` of ``_sre.SRE_Pattern``
    :param async_start: Enable driver asynchronous start within an environment.
    :type async_start: ``bool``

    Also inherits all
    :py:class:`~testplan.common.entity.base.Resource` options.
    """

    CONFIG = DriverConfig

    def __init__(self, **options):
        super(Driver, self).__init__(**options)
        self.extracts = {}
        self.file_logger = None

    @property
    def name(self):
        """Driver name."""
        return self.cfg.name

    def uid(self):
        """Driver uid."""
        return self.cfg.name

    def pre_start(self):
        """Callable to be executed right before driver starts."""

    def post_start(self):
        """Callable to be executed right after driver starts."""

    def started_check(self, timeout=None):
        """Driver started status condition check."""
        wait(lambda: self.extract_values(), self.cfg.timeout,
             raise_on_timeout=True)

    def pre_stop(self):
        """Callable to be executed right before driver stops."""

    def post_stop(self):
        """Callable to be executed right after driver stops."""

    def stopped_check(self, timeout=None):
        """Driver stopped status condition check."""

    def starting(self):
        """Trigger driver start."""
        self.make_runpath_dirs()
        self.pre_start()

    def stopping(self):
        """Trigger driver stop."""
        self.pre_stop()

    def _wait_started(self, timeout=None):
        self.started_check(timeout=timeout)
        self.status.change(self.STATUS.STARTED)
        self.post_start()

    def _wait_stopped(self, timeout=None):
        self.stopped_check(timeout=timeout)
        self.status.change(self.STATUS.STOPPED)
        self.post_stop()

    def context_input(self):
        """Driver context information."""
        return {attr: getattr(self, attr) for attr in dir(self)}

    @property
    def logpath(self):
        """Path for log regex matching."""
        return None

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
                (self.logpath, self.cfg.log_regexps, log_unmatched))
        if self.outpath and self.cfg.stdout_regexps:
            regex_sources.append(
                (self.outpath, self.cfg.stdout_regexps, stdout_unmatched))
        if self.errpath and self.cfg.stderr_regexps:
            regex_sources.append(
                (self.errpath, self.cfg.stderr_regexps, stderr_unmatched))

        for outfile, regexps, unmatched in regex_sources:
            file_result, file_extracts, file_unmatched = match_regexps_in_file(
                logpath=outfile,
                log_extracts=regexps,
                return_unmatched=True
            )
            unmatched.extend(file_unmatched)
            self.extracts.update(file_extracts)
            result = result and file_result

        if log_unmatched or stdout_unmatched or stderr_unmatched:

            err = (
                "Timed out starting {}({}):"
                " unmatched log_regexps in {}."
            ).format(type(self).__name__, self.name, self.logpath)

            err += format_regexp_matches(
                name='log_regexps',
                regexps=self.cfg.log_regexps,
                unmatched=log_unmatched
            )

            err += format_regexp_matches(
                name='stdout_regexps',
                regexps=self.cfg.stdout_regexps,
                unmatched=stdout_unmatched
            )

            err += format_regexp_matches(
                name='stderr_regexps',
                regexps=self.cfg.stderr_regexps,
                unmatched=stderr_unmatched
            )

            if self.extracts:
                err += '{newline}Matching groups:{newline}'.format(
                    newline=os.linesep)
                err += os.linesep.join([
                    '\t{}: {}'.format(key, value)
                    for key, value in self.extracts.items()
                ])
            return FailedAction(error_msg=err)
        return result

    def _install_target(self):
        raise NotImplementedError()

    def _install_files(self):
        for template in self.cfg.install_files:
            instantiate(template, self.context_input(), self._install_target())

    def _setup_file_logger(self, path):
        formatter = logging.Formatter('%(asctime)s %(levelname)s %(message)s')
        handler = logging.FileHandler(path)
        handler.setFormatter(formatter)
        logger = logging.getLogger('FileLogger_{}'.format(self.cfg.name))
        logger.addHandler(handler)
        logger.setLevel(self.logger.getEffectiveLevel())
        self.file_logger = logger
        self.file_logger.propagate = False  # No console logs

