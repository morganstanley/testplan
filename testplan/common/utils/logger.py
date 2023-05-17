"""
This module provides an interface from testplan to the standard python
logging module. It defines some extra logging levels and handles setting up
separate handlers for logging to stdout and to a file under the runpath.

The logging facility is used for:
    - Overall Testplan status
    - Driver status updates & logs
    - Worker & pool messages
    - Test progress information (e.g. Pass / Fail status)
    - Exporter statuses
"""
import os
import sys
import logging

from testplan.common.utils.strings import Color, uuid4
from testplan.report import Status

# Define our log-level constants. We add some extra levels between INFO and
# WARNING.
CRITICAL = logging.CRITICAL  # 50
ERROR = logging.ERROR  # 40
WARNING = logging.WARNING  # 30
USER_INFO = 25
INFO = logging.INFO  # 20
DEBUG = logging.DEBUG  # 10

LOGGER_NAME = "TESTPLAN"
LOGFILE_NAME = "testplan.log"
LOGFILE_FORMAT = (
    "%(asctime)-24s %(processName)-12s %(threadName)-12s "
    "%(name)-30s %(levelname)-15s %(message)s"
)


class TestplanLogger(logging.Logger):
    """
    Custom Logger class for Testplan. Adds extra logging level and
    corresponding method for USER_INFO.
    """

    _TEST_STATUS_FORMAT = "%(indent)s[%(name)s] -> %(pass_label)s"

    # In addition to the built-in log levels, we add some extras.
    _CUSTOM_LEVELS = {
        level_name: globals()[level_name] for level_name in ("USER_INFO",)
    }
    # As well as storing the log levels as global constants, we also store them
    # all in a dict on this class. This is useful for enumerating all valid
    # log levels.
    LEVELS = _CUSTOM_LEVELS.copy()
    LEVELS.update(
        {
            level_name: globals()[level_name]
            for level_name in ("CRITICAL", "ERROR", "WARNING", "INFO", "DEBUG")
        }
    )

    def __init__(self, *args, **kwargs):
        """
        Initialise the logger and add our custom log levels and methods to
        log at each level.
        """
        super(TestplanLogger, self).__init__(*args, **kwargs)

        # Add our custom levels. We could easily set partial functions here to
        # log at each level, but by defining these methods statically on the
        # class they can be included in the API docs.
        for level_name, level in self._CUSTOM_LEVELS.items():
            logging.addLevelName(level_name, level)

    def user_info(self, msg, *args, **kwargs):
        """Log 'msg % args' with severity 'USER_INFO'"""
        self._custom_log(USER_INFO, msg, *args, **kwargs)

    def log_test_status(self, name, status, indent=0, level=USER_INFO):
        """Shortcut to log a pass/fail status for a test."""
        if Status.STATUS_CATEGORY[status] == Status.PASSED:
            pass_label = Color.green(status.title())
        elif Status.STATUS_CATEGORY[status] in [Status.FAILED, Status.ERROR]:
            pass_label = Color.red(status.title())
        elif Status.STATUS_CATEGORY[status] == Status.UNSTABLE:
            pass_label = Color.yellow(status.title())
        else:  # unknown
            pass_label = status

        indent_str = indent * " "
        msg = self._TEST_STATUS_FORMAT
        self._custom_log(
            level,
            msg,
            {"name": name, "pass_label": pass_label, "indent": indent_str},
        )

    def _custom_log(self, level, msg, *args, **kwargs):
        """Log 'msg % args' with severity 'level'."""
        if self.isEnabledFor(level):
            self._log(level, msg, args, **kwargs)


def _initial_setup():
    """
    Perform initial setup for the logger. Creates and adds a handler to log
    to stdout with default level USER_INFO.

    :return: root logger object and stdout logging handler
    :type: ``tuple``
    """
    logging.setLoggerClass(TestplanLogger)
    root_logger = logging.getLogger(LOGGER_NAME)

    # Set the level of the root logger to DEBUG so that nothing is filtered out
    # by the logger itself - the handlers will perform filtering.
    root_logger.setLevel(DEBUG)

    # Set up the stdout log handler. This handler just writes messages out to
    #  stdout without any extra formatting and is intended for user-facing
    # logs. The level is controlled by command-line args so should be set
    # when those args are parsed; however to begin with we set the level to
    # USER_INFO as a default.
    stdout_handler = logging.StreamHandler(sys.stdout)
    stdout_formatter = logging.Formatter("%(message)s")
    stdout_handler.setFormatter(stdout_formatter)
    stdout_handler.setLevel(USER_INFO)
    root_logger.addHandler(stdout_handler)
    root_logger.propagate = False

    return root_logger, stdout_handler


# Ideally, objects should log by inheriting from "Loggable" and using
# self.logger. However, for classes that don't inherit from Loggable or for
# code outside of a class we provide the root testplan.common.utils.logger
# object here as TESTPLAN_LOGGER.
TESTPLAN_LOGGER, STDOUT_HANDLER = _initial_setup()


def configure_file_logger(level, runpath):
    """
    Configure the file logger.

    :param level: Logging level - should be one of the values in
                  TestplanLogger.LEVELS.
    :type level: ``int``
    :param runpath: top-level runpath - the log file will be created in here.
    :type runpath: ``str``
    """
    if level not in TestplanLogger.LEVELS.values():
        raise ValueError(
            "Unexpected log level {level} - expected one of {expected}".format(
                level=level, expected=TestplanLogger.LEVELS.values()
            )
        )

    logfile_path = os.path.join(runpath, LOGFILE_NAME)

    # Try to set up the file handler. The file log is intended for
    # debugging purposes, both for internal testplan issues and issues in
    # user's code. We specify a formatter to add additional information
    # useful for debugging.
    try:
        file_handler = logging.FileHandler(logfile_path, encoding="utf-8")
    except IOError as err:
        # If we cannot open the logfile for any reason just continue
        # regardless, but log the error (it will go to stdout).
        TESTPLAN_LOGGER.error(
            "Cannot open log file at %s for writing: %s", logfile_path, err
        )
        return None
    else:
        file_handler.setLevel(level)
        formatter = logging.Formatter(LOGFILE_FORMAT)
        file_handler.setFormatter(formatter)
        TESTPLAN_LOGGER.addHandler(file_handler)

        TESTPLAN_LOGGER.debug("Enabled logging to file: %s", logfile_path)
        return file_handler


class Loggable:
    """
    Base class that allows an object to log via self.logger. The advantage of
    objects having their own logger over using a single global logger is that
    the logger name can be used to identify which class the logs originate
    from. Loggers are hierarchical so logs made from a child will bubble up
    to the parent - all logs will be ultimately handled by the root testplan
    logger and its associated handlers.
    """

    def __init__(self):
        """
        Adds a new logger to this object. The logger name must begin with
        "testplan." to ensure that the logs bubble up to the root testplan
        logger.
        """
        # The full module path + class name for a class can be quite long and
        # take up a lot of space in the logfile. For brevity we just use
        # "testplan.<class name>" as the logger name, since class names are
        # mostly unique.

        self._logger = None
        super(Loggable, self).__init__()

    @property
    def logger(self) -> TestplanLogger:
        """logger object"""
        # Define logger as a property instead of self.logger directly.
        # This is to workaround a python2 issue that logger object cannot be
        # pickled/deepcopied, but we need to do that for task target which
        # could be a multitest object.

        if self._logger:
            return self._logger

        self._logger = logging.getLogger(f"{LOGGER_NAME}.{self}")
        return self._logger

    @property
    def _debug_logging_enabled(self):
        """
        :return: True if the logging level is DEBUG (or lower) for the stdout
            handler. We don't consider the file handler because that always
            logs at DEBUG level.
        :rtype: ``bool``
        """
        return STDOUT_HANDLER.level <= DEBUG
