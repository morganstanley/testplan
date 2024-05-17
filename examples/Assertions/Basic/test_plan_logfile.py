#!/usr/bin/env python
"""
This example shows usage of Logfile namespace assertions.
"""
import os
import sys
import threading
import time

import zmq

from testplan import test_plan
from testplan.common.utils.context import context
from testplan.common.utils.match import LogMatcher
from testplan.report.testing.styles import Style, StyleEnum
from testplan.testing.multitest import MultiTest, testcase, testsuite, xfail
from testplan.testing.multitest.driver import Driver
from testplan.testing.multitest.driver.zmq import ZMQClient


class CustomZMQServer(Driver):
    """
    Custom ZMQ server driver which logs received message to a logfile.
    """

    def __init__(self, name, logname):
        super().__init__(name)
        self.logname = logname
        self.port = None

    @property
    def logpath(self):
        return os.path.join(self.runpath, self.logname)

    def starting(self):
        super().starting()
        self._log = open(self.logpath, "wb+")
        self._sig = threading.Event()
        self._thr = threading.Thread(target=self._start_loop)
        self._thr.start()

    def _start_loop(self):
        self._ctx = zmq.Context()
        self._soc = self._ctx.socket(zmq.PAIR)
        self.port = self._soc.bind_to_random_port("tcp://0.0.0.0")
        while True:
            if self._sig.is_set():
                self._soc.close()
                self._ctx.term()
                break
            try:
                msg = self._soc.recv(zmq.NOBLOCK)
                self._log.write(msg)
                self._log.flush()
            except zmq.ZMQError:
                time.sleep(0.1)
                continue

    def stopping(self):
        super().stopping()
        self._sig.set()
        self._thr.join()
        self._log.close()


@testsuite
class LogfileSuite:
    @testcase
    def match_logfile(self, env, result):
        # Create LogMatcher on target logfile, in practice driver could be
        # shipped with a LogMatcher which can be used here.
        lm = LogMatcher(env.server.logpath, binary=True)

        # Client sending message, which is expected to be appeared in server
        # log soon.
        env.client.send(b"ping\n")
        result.logfile.match(lm, r"ping", description="first assertion")

        # Flood server log with irrelevant messages.
        for _ in range(10):
            env.client.send(b"pong\n")
        result.logfile.seek_eof(lm, description="second assertion")
        for _ in range(10):
            env.client.send(b"pong\n")

        # With ``seek_eof`` operation embedded in context manager, it should
        # take quite little time to find our newly generated message.
        with result.logfile.expect(lm, r"ping", description="third assertion"):
            env.client.send(b"ping\n")

    @xfail("failed assertion demo")
    @testcase
    def match_logfile_xfail(self, env, result):
        lm = LogMatcher(env.server.logpath, binary=True)
        with result.logfile.expect(
            lm, r"pong", description="first assertion", timeout=0.2
        ):
            env.client.send(b"ping")


@test_plan(
    name="Logfile Assertion Example",
    stdout_style=Style(
        passing=StyleEnum.ASSERTION_DETAIL, failing=StyleEnum.ASSERTION_DETAIL
    ),
)
def main(plan):
    plan.add(
        MultiTest(
            name="Logfile Assertion Test",
            suites=[
                LogfileSuite(),
            ],
            environment=[
                CustomZMQServer(name="server", logname="zmq_received"),
                ZMQClient(
                    name="client",
                    message_pattern=zmq.PAIR,
                    hosts=["localhost"],
                    ports=[context("server", "{{port}}")],
                ),
            ],
        )
    )


if __name__ == "__main__":
    sys.exit(not main())
