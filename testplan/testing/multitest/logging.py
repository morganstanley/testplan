from __future__ import absolute_import

import logging
from collections import namedtuple
from contextlib import contextmanager
from six import StringIO
from logging import StreamHandler
from tempfile import NamedTemporaryFile

from testplan.common.utils.logger import _LOGFILE_FORMAT, Loggable

CAPTURED_LOG_DESCRIPTION = "Auto Captured Log"


class CaptureLevel(object):
    """Capture level Enum like object

    ROOT:
        Capture all logs reaching the root logger, it contains all testplan logs plus other lib logs
    TESTPLAN:
        Capture all testplan logs, eg driver logs
    TESTSUITE:
        Whatever is logged from the testcases
    """

    ROOT = staticmethod(lambda suite: logging.getLogger())
    TESTPLAN = staticmethod(lambda suite: suite.logger.parent)
    TESTSUITE = staticmethod(lambda suite: suite.logger)


class LogCaptureConfig(object):
    """
    Configuration for log capture

    Attributes
    ----------
    capture_level CaptureLevel:
        initial value: CaptureLevel.TESTSUITE The level the log are captured, TESTSUITE (default), TESTPLAN or ROOT
    attach_log bool:
        If True the logs captured to file and then attached to the result
    format str:
        A format string can be passed to the loghandler


    """

    def __init__(self):
        self.capture_level = CaptureLevel.TESTSUITE
        self.attach_log = False
        self.format = _LOGFILE_FORMAT


class LogCaptureMixin(Loggable):
    """ Mixin to add easy logging support to any @multitest.testsuite

    """

    _LogCaptureInfo = namedtuple(
        "LogCaptureInfo", ["result", "handler", "attach_file", "capture_level"]
    )

    def __init__(self):
        super(LogCaptureMixin, self).__init__()
        self.__log_capture_config = LogCaptureConfig()

    @property
    def log_capture_config(self):
        return self.__log_capture_config

    @log_capture_config.setter
    def log_capture_config(self, value):
        return self.__log_capture_config == value

    def _attach_handler(
        self,
        result,
        capture_level_override=None,
        attach_log_override=None,
        format_override=None,
    ):
        def override(value, _with):
            return value if _with is None else _with

        capture_level = override(
            self.log_capture_config.capture_level, capture_level_override
        )
        save_to_file = override(
            self.log_capture_config.attach_log, attach_log_override
        )
        format_string = override(
            self.log_capture_config.format, format_override
        )

        if save_to_file:
            stream = NamedTemporaryFile(
                "w+t", dir=result._scratch, suffix=".log", delete=False
            )
        else:
            stream = StringIO()

        handler = StreamHandler(stream)
        handler.setFormatter(logging.Formatter(format_string))

        logger = self.select_logger(capture_level)

        logger.addHandler(handler)

        return self._LogCaptureInfo(
            result, handler, save_to_file, capture_level
        )

    def _detach_handler(self, log_capture_info):
        self.select_logger(log_capture_info.capture_level).removeHandler(
            log_capture_info.handler
        )
        log_capture_info.handler.flush()
        log_capture_info.handler.close()
        if log_capture_info.attach_file:
            log_capture_info.result.attach(
                log_capture_info.handler.stream.name, CAPTURED_LOG_DESCRIPTION
            )
        else:
            log_capture_info.result.log(
                log_capture_info.handler.stream.getvalue(),
                CAPTURED_LOG_DESCRIPTION,
            )

    @contextmanager
    def capture_log(
        self, result, capture_level=None, attach_log=None, format=None
    ):
        """Context manager to capture logs, capture the log in the provided result.

        :param result: The result where to inject the log
        :param CaptureLevel capture_level:  The level the log are captured, TESTSUITE (default), TESTPLAN or ROOT
        :param bool attach_log: If True the logs captured to file and then attached to the result
        :param str format: A format string can be passed to the loghandler
        :return: returns the suite level logger
        :rtype: logging.Logger
        """
        try:
            info = self._attach_handler(
                result,
                capture_level_override=capture_level,
                attach_log_override=attach_log,
                format_override=format,
            )

            yield self.logger
        finally:
            self._detach_handler(info)

    def select_logger(self, capture_level):
        return capture_level(self)


class AutoLogCaptureMixin(LogCaptureMixin):
    def __init__(self):
        super(AutoLogCaptureMixin, self).__init__()
        self._state = None

    def pre_testcase(self, name, env, result):
        self._state = self._attach_handler(result)

    def post_testcase(self, name, env, result):
        self._detach_handler(self._state)
