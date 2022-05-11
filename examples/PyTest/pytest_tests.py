"""Example test script for use by PyTest."""
# For the most basic usage, no imports are required.
# pytest will automatically detect any test cases based
# on methods starting with ``test_``.
import os

import pytest

from testplan.testing.multitest.result import Result


class TestPytestBasics:
    """
    Demonstrate the basic usage of PyTest. PyTest testcases can be declared
    as either plain functions or methods on a class. Testcase functions or
    method names must begin with "test" and classes containing testcases
    must being with "Test".

    Classes containing testcases must not define an __init__() method. The
    recommended way to perform setup is to make use of Testplan's Environment -
    see the "TestWithDrivers" example below. Pytest fixtures and the older
    xunit-style setup() and teardown() methods may also be used.
    """

    def test_success(self):
        """
        Trivial test method that will simply cause the test to succeed.
        Note the use of the plain Python assert statement.
        """
        assert True

    def test_failure(self):
        """
        Similar to above, except this time the test case will always fail.
        """
        print("test output")
        assert False

    @pytest.mark.parametrize("a,b,c", [(1, 2, 3), (-1, -2, -3), (0, 0, 0)])
    def test_parametrization(self, a, b, c):
        """Parametrized testcase."""
        assert a + b == c


class TestWithDrivers:
    """
    MultiTest drivers are also available for PyTest.
    The testcase can access those drivers by parameter `env`,
    and make assertions provided by `result`.
    """

    def test_drivers(self, env, result):
        """Testcase using server and client objects from the environment."""
        message = "This is a test message"
        env.server.accept_connection()
        size = env.client.send(bytes(message.encode("utf-8")))
        received = env.server.receive(size)
        result.log(
            "Received Message from server: {}".format(received),
            description="Log a message",
        )
        result.equal(
            received.decode("utf-8"), message, description="Expect a message"
        )


class TestWithAttachments:
    def test_attachment(self, result: Result):
        result.attach(__file__, "example attachment")

class TestPytestMarks:
    """
    Demonstrate the use of Pytest marks. These can be used to skip a testcase,
    or to run it but expect it to fail. Marking testcases in this way is a
    useful way to skip running them in situations where it is known to fail -
    e.g. on a particular OS or python interpreter version - or when a testcase
    is added before the feature is implemented in TDD workflows.
    """

    @pytest.mark.skip
    def test_skipped(self):
        """
        Tests can be marked as skipped and never run. Useful if the test is
        known to cause some bad side effect (e.g. crashing the python
        interpreter process).
        """
        raise RuntimeError("Testcase should not run.")

    @pytest.mark.skipif(os.name != "posix", reason="Only run on Linux")
    def test_skipif(self):
        """
        Tests can be conditionally skipped - useful if a test should only be
        run on a specific platform or python interpreter version.
        """
        assert os.name == "posix"

    @pytest.mark.xfail
    def test_xfail(self):
        """
        Tests can alternatively be marked as "xfail" - expected failure. Such
        tests are run but are not reported as failures by Testplan. Useful
        for testing features still under active development, or for unstable
        tests so that you can keep running and monitoring the output without
        blocking CI builds.
        """
        raise NotImplementedError("Testcase expected to fail")

    @pytest.mark.xfail(raises=NotImplementedError)
    def test_unexpected_error(self):
        """
        Optionally, the expected exception type raised by a testcase can be
        specified. If a different exception type is raised, the testcase will
        be considered as failed. Useful to ensure that a test fails for the
        reason you actually expect it to.
        """
        raise TypeError("oops")

    @pytest.mark.xfail
    def test_xpass(self):
        """
        Tests marked as xfail that don't actually fail are considered an
        XPASS by PyTest, and Testplan considers the testcase to have passed.
        """
        assert True

    @pytest.mark.xfail(strict=True)
    def test_xpass_strict(self):
        """
        If the strict parameter is set to True, tests marked as xfail will be
        considered to have failed if they pass unexpectedly.
        """
        assert True
