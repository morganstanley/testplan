"""An unstable tests to be executed until pass."""

import os

from testplan.testing.multitest import MultiTest, testsuite, testcase
from testplan.common.utils.path import makedirs


@testsuite
class Unstablesuite(object):
    """
    A test suite which has an unstable testcase.
    The multitest containing this suite has to re-run twice
    (3 times in total) in order to get passed.
    """

    def __init__(self, tmp_file):
        self._iteration = None
        self._max_rerun = 2
        self._tmp_file = tmp_file

    def setup(self, env, result):
        """
        Create a tmp text file which record how many times the suite
        has been executed, should remove it after the last rerun.
        """
        makedirs(os.path.dirname(self._tmp_file))
        if not os.path.exists(self._tmp_file):
            self._iteration = 0
        else:
            with open(self._tmp_file, "r") as fp:
                self._iteration = int(fp.read())

        if self._iteration == self._max_rerun:
            os.remove(self._tmp_file)
        else:
            with open(self._tmp_file, "w") as fp:
                fp.write(str(self._iteration + 1))

        result.log("Suite setup in iteration {}".format(self._iteration))

    @testcase
    def unstable_testcase(self, env, result):
        """
        An unstable testcase which can only pass at 3rd run (2nd rerun).
        """
        if self._iteration == 2:
            result.log("Test passes")
        else:
            result.fail("Test fails")


def make_multitest(tmp_file):
    """
    Creates a new MultiTest that runs unstable tests.
    """
    return MultiTest(
        name="UnstableMultiTest",
        suites=[Unstablesuite(tmp_file=tmp_file)],
        environment=[],
    )
