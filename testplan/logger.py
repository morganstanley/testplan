"""
    This module contains the logic for creating/filtering
    stdout during a Testplan run.

    It includes:
        - Overall Testplan status
        - Driver status updates & logs
        - Worker & pool messages
        - Test progress information (e.g. Pass / Fail status)
        - Exporter statuses
"""

import sys
import logging
from testplan.common.utils.strings import Color


CRITICAL = logging.CRITICAL  # 50
ERROR = logging.ERROR  # 40
WARNING = logging.WARNING  # 30
EXPORTER_INFO = 29
TEST_INFO = 28
DRIVER_INFO = 27
INFO = logging.INFO  # 20
DEBUG = logging.DEBUG  # 10


def attach_log_method(method_name, level, level_name):

    if hasattr(logging.Logger, method_name):
        raise AttributeError(
            'Cannot overwrite logger method: {}'.format(method_name))

    logging.addLevelName(level_name, level)

    def method(self, message, *args, **kwargs):
        if self.isEnabledFor(level):
            self._log(level, message, args, **kwargs)

    method.__name__ = method_name

    setattr(logging.Logger, method_name, method)


attach_log_method('test_info', TEST_INFO, 'TEST_INFO')
attach_log_method('driver_info', DRIVER_INFO, 'DRIVER_INFO')
attach_log_method('exporter_info', EXPORTER_INFO, 'EXPORTER_INFO')


TEST_STATUS_FORMAT = '[{name}] -> {pass_label}'

TESTPLAN_LOGGER = logging.getLogger('testplan')

# TODO: Add custom config support
TESTPLAN_LOGGER.setLevel(TEST_INFO)

logging.basicConfig(stream=sys.stdout, format='%(message)s')


def get_test_status_message(name, passed):
    pass_label = Color.green('Pass') if passed else Color.red('Fail')
    return TEST_STATUS_FORMAT.format(name=name, pass_label=pass_label)


def log_test_status(name, passed):
    TESTPLAN_LOGGER.test_info(get_test_status_message(name, passed))
