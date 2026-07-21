"""Functional tests for the PyTest test runner wrapper."""

import os

import pytest

from testplan import TestplanMock
from testplan.common.utils import logger
from testplan.common.utils.context import context
from testplan.report import Status
from testplan.testing.multitest.driver.tcp import TCPClient, TCPServer
from testplan.testing.py_test import PyTest


@pytest.fixture
def mockplan_default_log_level(runpath):
    """
    mockplan with logger level reset to USER_INFO
    """
    yield TestplanMock("plan", logger_level=logger.USER_INFO, runpath=runpath)


@pytest.fixture
def pytest_test_inst(repo_root_path, root_directory):
    """Return a PyTest test instance, with the example tests as its target."""
    # For testing purposes, we want to run the pytest example at
    # examples/PyTest/pytest_tests.py.
    example_path = os.path.join(
        repo_root_path, "examples", "PyTest", "pytest_tests.py"
    )

    rootdir = os.path.commonprefix([root_directory, os.getcwd()])

    return PyTest(
        name="My PyTest",
        description="PyTest example test",
        target=example_path,
        extra_args=["--rootdir", rootdir],
        environment=[
            TCPServer(name="server", host="localhost", port=0),
            TCPClient(
                name="client",
                host=context("server", "{{host}}"),
                port=context("server", "{{port}}"),
            ),
        ],
    )


def test_assertion_recorded(mockplan_default_log_level, pytest_test_inst):
    mockplan_default_log_level.schedule(pytest_test_inst, runner=None)
    assert mockplan_default_log_level.run().run is True
    # NOTE: ref change within _ReportPlugin
    failed_assr = mockplan_default_log_level.report["My PyTest"][
        "pytest_tests.py::TestPytestBasics"
    ]["test_failure"][0]
    assert failed_assr["description"] != "Exception raised", (
        "PyTest wrapper issue reoccurred"
    )
    assert mockplan_default_log_level.report.status == Status.FAILED
