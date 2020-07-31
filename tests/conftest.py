"""Shared PyTest fixtures."""

import os
import pytest
from testplan import TestplanMock


@pytest.fixture(scope="function")
def runpath(tmp_path):
    """
    Return a temporary runpath for testing. The path will not be automatically
    removed after the test for easier investigation.

    It takes a form like: /tmp/pytest-of-userid/pytest-151/test_sub_pub_unsub0
    """
    return str(tmp_path)


@pytest.fixture(scope="function")
def mockplan(runpath):
    """
    Return a temporary TestplanMock for testing. Some components needs a
    testplan for getting runpath and cfg.
    """
    mockplan = TestplanMock("plan", runpath=runpath)
    return mockplan


@pytest.fixture(scope="session")
def repo_root_path():
    """
    Return the path to the root of the testplan repo as a string. Useful
    for building paths to specific files/directories in the repo without
    relying on the current working directory or building a relative path from
    a different known filepath.
    """
    # This file is at tests/conftest.py. It should not be moved, since it
    # defines global pytest fixtures for all tests.
    return os.path.join(os.path.dirname(__file__), os.pardir)


@pytest.fixture(scope="session")
def root_directory(pytestconfig):
    """
    Return the root directory of pyTest config as a string.
    """
    return str(pytestconfig.rootdir)
