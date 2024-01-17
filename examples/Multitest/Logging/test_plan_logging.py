import logging

from testplan import test_plan
from testplan.common.report.base import Status
from testplan.report.testing.styles import Style, StyleEnum
from testplan.testing.base import ASSERTION_INDENT
from testplan.testing.multitest import MultiTest, testsuite, testcase
from testplan.testing.multitest.logging import (
    CaptureLevel,
    LogCaptureMixin,
    AutoLogCaptureMixin,
)


@testsuite
class LoggingSuite(LogCaptureMixin):
    """
    Demonstrate how logging can added to testcase and possibly captured in the result from test suite.
    Add LogCaptureMixin and self.logger will be available for logging. self.capture_log(result) can be
    used as a context manager to capture log in the result. It is possible to format the log as needed,
    and also to attach the captured log as a file.

    The log can be captured at 3 leveles, -TESTSUITE: only the logs logged through self.logger will be captured,
    -TESTPLAN: all testplan related loggs captured (so drivers logs will be included as well), -ROOT: all logs
    will be captured at the level the root logger is set normally WARNING
    """

    @testcase
    def testsuite_level(self, env, result):
        with self.capture_log(
            result
        ) as logger:  # as convenience the logger is returned but is is really the same as
            logger.info("Hello")
            self.logger.info("Logged as well")
            self.logger.parent.info("Not captured")
            logging.getLogger().warning("Not captured either")

    @testcase
    def testplan_level(self, env, result):
        with self.capture_log(
            result, capture_level=CaptureLevel.TESTPLAN
        ) as logger:
            logger.info("Hello")
            self.logger.info("Logged as well")
            self.logger.parent.info("Now captured")
            logging.getLogger().warning("Not captured either")

    @testcase
    def root_level(self, env, result):
        with self.capture_log(
            result, capture_level=CaptureLevel.ROOT
        ) as logger:
            logger.info("Hello")
            self.logger.info("Logged as well")
            self.logger.parent.info("Now captured")
            logging.getLogger().warning("This captured too")

    @testcase
    def attach(self, env, result):
        with self.capture_log(result, attach_log=True) as logger:
            logger.info("Attached Log")

    @testcase
    def format(self, env, result):
        with self.capture_log(
            result,
            format="%(asctime)-24s %(name)-50s %(levelname)-15s %(message)s",
        ) as logger:
            logger.info("Formatted")

    @testcase
    def multiple(self, env, result):
        with self.capture_log(result):
            self.logger.info("CaptureGroup 1")
            self.logger.error(
                "To have some color"
            )  # This level goes to stdout too

        # do an assertion to separate the blocks
        result.true(True, "This is so true")

        with self.capture_log(result):
            self.logger.info("CaptureGroup 2")
            self.logger.warning(
                "To have some color"
            )  # This level goes to stdout too

    @testcase
    def specials(self, env, result):
        with self.capture_log(result):
            self.logger.user_info("Test info log: goes to the console as well")
            self.logger.log_test_status(
                "A mandatory check", Status.PASSED, indent=ASSERTION_INDENT
            )


@testsuite
class AutoLoggingSuite(AutoLogCaptureMixin):
    """
    AutoLogCaptureMixin will automatically add captured log at the end of all testcase
    """

    @testcase
    def case(self, env, result):
        self.logger.info("Hello")

    @testcase
    def case2(self, env, result):
        self.logger.info("Do it for all the testcases")


@testsuite
class AutoLoggingSuiteThatAttach(AutoLogCaptureMixin):
    def __init__(self):
        super(AutoLoggingSuiteThatAttach, self).__init__()
        self.log_capture_config.attach_log = True

    @testcase
    def case(self, env, result):
        self.logger.info("Hello Attached")


@testsuite
class AutoLoggingSuiteThatFormat(AutoLogCaptureMixin):
    def __init__(self):
        super(AutoLoggingSuiteThatFormat, self).__init__()
        self.log_capture_config.format = (
            "%(asctime)-24s %(name)-50s %(levelname)-15s %(message)s"
        )

    @testcase
    def case(self, env, result):
        self.logger.info("Hello Formatted")


@test_plan(
    name="Logging",
    pdf_path="report.pdf",
    pdf_style=Style(
        passing=StyleEnum.ASSERTION_DETAIL, failing=StyleEnum.ASSERTION_DETAIL
    ),
)
def main(plan):
    plan.add(
        MultiTest(
            name="Logging",
            suites=[
                LoggingSuite(),
                AutoLoggingSuite(),
                AutoLoggingSuiteThatAttach(),
                AutoLoggingSuiteThatFormat(),
            ],
        )
    )


if __name__ == "__main__":
    main()
