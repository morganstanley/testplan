import re
import six
import logging
import pytest

if six.PY2:
    import mock
else:
    from unittest import mock

import testplan
from testplan.testing import multitest
from testplan.testing.filtering import Pattern, Filter
from testplan.testing.multitest.logging import (
    LogCaptureMixin,
    CaptureLevel,
    AutoLogCaptureMixin,
)

SIMPLE_LOG = "Simple log"
LOGGER_LEVEL_PATTERN = r"([^ ]*) *([^ ]*) *{}$".format(SIMPLE_LOG)


@multitest.testsuite
class LoggingSuite(LogCaptureMixin):
    @multitest.testcase
    def just_log(self, env, result):
        self.logger.info(SIMPLE_LOG)

    @multitest.testcase
    def capture_log_single_scope(self, env, result):
        with self.capture_log(result):
            self.logger.info(SIMPLE_LOG)

    @multitest.testcase
    def capture_log_multiple_scope(self, env, result):
        with self.capture_log(result):
            self.logger.info(SIMPLE_LOG + "1")
        result.true(True)
        with self.capture_log(result):
            self.logger.info(SIMPLE_LOG + "2")

    @multitest.testcase
    def testsuite_level(self, env, result):
        with self.capture_log(result, capture_level=CaptureLevel.TESTSUITE):
            self.logger.info(SIMPLE_LOG)
            self.logger.parent.debug(SIMPLE_LOG)
            logging.getLogger().warning(SIMPLE_LOG)

    @multitest.testcase
    def testplan_level(self, env, result):
        with self.capture_log(result, capture_level=CaptureLevel.TESTPLAN):
            self.logger.info(SIMPLE_LOG)
            self.logger.parent.debug(SIMPLE_LOG)
            logging.getLogger().warning(SIMPLE_LOG)

    @multitest.testcase
    def root_level(self, env, result):
        with self.capture_log(result, capture_level=CaptureLevel.ROOT):
            self.logger.info(SIMPLE_LOG)
            self.logger.parent.debug(SIMPLE_LOG)
            logging.getLogger().warning(SIMPLE_LOG)

    @multitest.testcase
    def attach_log(self, env, result):
        with self.capture_log(result, attach_log=True):
            self.logger.info(SIMPLE_LOG)


@multitest.testsuite
class AutoLoggingSuite(AutoLogCaptureMixin):
    @multitest.testcase
    def auto_log_capture(self, env, result):
        self.logger.info(SIMPLE_LOG)


logging_suite, auto_logging_suite = LoggingSuite(), AutoLoggingSuite()


@pytest.fixture
def suites():
    return [logging_suite, auto_logging_suite]


@pytest.fixture
def get_filtered_plan(suites):
    def _factory(pattern=None):
        plan = testplan.TestplanMock(
            name="Logging TestPlan",
            test_filter=Pattern(pattern) if pattern else Filter(),
        )
        plan.add(multitest.MultiTest(name="Logging Test", suites=suites))
        return plan

    return _factory


class LoggerSpy(object):
    def __init__(self, name=None, logger_obj=None):
        logger = logger_obj or logging.getLogger(name)
        self.patcher = {}
        for method in ["info", "debug", "warning"]:
            self.patcher[method] = mock.patch.object(
                logger, method, wraps=logger.__getattribute__(method)
            )

    def __enter__(self):
        for method, patcher in six.iteritems(self.patcher):
            self.__setattr__(method, patcher.__enter__())
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        for method, patcher in six.iteritems(self.patcher):
            patcher.__exit__(exc_type, exc_val, exc_tb)
            self.__delattr__(method)


@pytest.fixture
def suite_logger_spy():
    return LoggerSpy(logger_obj=logging_suite.logger)


@pytest.fixture
def auto_suite_logger_spy():
    return LoggerSpy(logger_obj=auto_logging_suite.logger)


@pytest.fixture
def testplan_logger_spy():
    return LoggerSpy(name="testplan")


@pytest.fixture
def root_logger_spy():
    return LoggerSpy(name="")


def get_case_result(plan_result):
    return plan_result.report.entries[0].entries[0].entries[0]


def test_logging(get_filtered_plan, suite_logger_spy):
    plan = get_filtered_plan("*:*:just_log")
    with suite_logger_spy as spy:
        plan.run()

        spy.info.assert_called_once_with(SIMPLE_LOG)


def test_capture_single_scope(get_filtered_plan, suite_logger_spy):
    # Given
    plan = get_filtered_plan("*:*:capture_log_single_scope")
    with suite_logger_spy as spy:
        # When
        plan_result = plan.run()

        # Then
        spy.info.assert_called_once_with(SIMPLE_LOG)

        case_result = get_case_result(plan_result)

        assert len(case_result.entries) == 1
        assert case_result.entries[0]["type"] == "Log"
        assert SIMPLE_LOG in case_result.entries[0]["message"]


def test_capture_multiple_scope(get_filtered_plan, suite_logger_spy):
    # Given
    plan = get_filtered_plan("*:*:capture_log_multiple_scope")
    with suite_logger_spy as spy:
        # When
        plan_result = plan.run()

        # Then
        assert spy.info.call_count == 2

        case_result = get_case_result(plan_result)

        assert len(case_result.entries) == 3
        assert case_result.entries[0]["type"] == "Log"
        assert SIMPLE_LOG + "1" in case_result.entries[0]["message"]
        assert case_result.entries[1]["type"] == "IsTrue"
        assert case_result.entries[2]["type"] == "Log"
        assert SIMPLE_LOG + "2" in case_result.entries[2]["message"]


def test_suite_level(
    get_filtered_plan, suite_logger_spy, testplan_logger_spy, root_logger_spy
):
    # Given
    plan = get_filtered_plan("*:*:testsuite_level")
    with suite_logger_spy as suite_spy, testplan_logger_spy as testplan_spy, root_logger_spy as root_spy:
        # When
        plan_result = plan.run()

        # Then all the logger got called
        suite_spy.info.assert_called_once_with(SIMPLE_LOG)
        testplan_spy.debug.assert_any_call(SIMPLE_LOG)
        root_spy.warning.assert_any_call(SIMPLE_LOG)

        # But the attached log has the suite level only
        case_result = get_case_result(plan_result)

        assert len(case_result.entries) == 1
        assert case_result.entries[0]["type"] == "Log"
        assert case_result.entries[0]["message"].count(SIMPLE_LOG) == 1


def test_plan_level(
    get_filtered_plan, suite_logger_spy, testplan_logger_spy, root_logger_spy
):
    # Given
    plan = get_filtered_plan("*:*:testplan_level")
    with suite_logger_spy as suite_spy, testplan_logger_spy as testplan_spy, root_logger_spy as root_spy:
        # When
        plan_result = plan.run()

        # Then all the logger got called
        suite_spy.info.assert_called_once_with(SIMPLE_LOG)
        testplan_spy.debug.assert_any_call(SIMPLE_LOG)
        root_spy.warning.assert_any_call(SIMPLE_LOG)

        # But the attached log has the suite level only
        case_result = get_case_result(plan_result)

        assert len(case_result.entries) == 1
        assert case_result.entries[0]["type"] == "Log"
        message = case_result.entries[0]["message"]
        assert message.count(SIMPLE_LOG) == 2
        result = re.findall(LOGGER_LEVEL_PATTERN, message, re.M)
        assert result[0][0].startswith("testplan.LoggingSuite")
        assert result[0][1] == "INFO"
        assert result[1:] == [("testplan", "DEBUG")]


def test_root_level(
    get_filtered_plan, suite_logger_spy, testplan_logger_spy, root_logger_spy
):
    # Given
    plan = get_filtered_plan("*:*:root_level")
    with suite_logger_spy as suite_spy, testplan_logger_spy as testplan_spy, root_logger_spy as root_spy:
        # When
        plan_result = plan.run()

        # Then all the logger got called
        suite_spy.info.assert_called_once_with(SIMPLE_LOG)
        testplan_spy.debug.assert_any_call(SIMPLE_LOG)
        root_spy.warning.assert_any_call(SIMPLE_LOG)

        # And the log has all 3 log in different level
        case_result = get_case_result(plan_result)

        assert len(case_result.entries) == 1
        assert case_result.entries[0]["type"] == "Log"
        message = case_result.entries[0]["message"]
        assert message.count(SIMPLE_LOG) == 3
        result = re.findall(LOGGER_LEVEL_PATTERN, message, re.M)
        assert result[0][0].startswith("testplan.LoggingSuite")
        assert result[0][1] == "INFO"
        assert result[1:] == [("testplan", "DEBUG"), ("root", "WARNING")]


def test_attach_log(get_filtered_plan, suite_logger_spy):
    # Given
    plan = get_filtered_plan("*:*:attach_log")
    with suite_logger_spy as spy:
        # When
        plan_result = plan.run()

        # The We have an attachment and it has the log
        spy.info.assert_called_once_with(SIMPLE_LOG)

        case_result = get_case_result(plan_result)

        assert len(case_result.entries) == 1
        assert case_result.entries[0]["type"] == "Attachment"
        assert len(case_result.attachments) == 1

        with open(case_result.attachments[0].source_path) as logfile:
            assert SIMPLE_LOG in logfile.readline()


def test_auto_log_capture(get_filtered_plan, auto_suite_logger_spy):
    # Given
    plan = get_filtered_plan("*:*:auto_log_capture")
    with auto_suite_logger_spy as spy:
        # When
        plan_result = plan.run()

        # Then
        spy.info.assert_called_once_with(SIMPLE_LOG)

        case_result = get_case_result(plan_result)

        assert len(case_result.entries) == 1
        assert case_result.entries[0]["type"] == "Log"
        assert SIMPLE_LOG in case_result.entries[0]["message"]
