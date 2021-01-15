"""Shared PyTest fixtures."""

import os
import sys

sys.path.append(os.path.join(os.path.dirname(__file__), 'helpers'))

import pytest
from testplan import TestplanMock
from testplan.common.utils import path


@pytest.fixture(scope="function")
def runpath():
    """
    Return a temporary runpath for testing. The path will be automatically
    removed after the test.

    We were originally using pytest builtin fixture tmp_path, which will create
    a path in a form like: /tmp/pytest-of-userid/pytest-151/test_sub_pub_unsub0
    But it has a known issue: https://github.com/pytest-dev/pytest/issues/5456
    """
    with path.TemporaryDirectory() as runpath:
        yield runpath


@pytest.fixture(scope="class")
def runpath_class():
    with path.TemporaryDirectory() as runpath:
        yield runpath


@pytest.fixture(scope="module")
def runpath_module():
    with path.TemporaryDirectory() as runpath:
        yield runpath


@pytest.fixture(scope="function")
def mockplan():
    """
    Return a temporary TestplanMock for testing. Some components needs a
    testplan for getting runpath and cfg.
    """
    with path.TemporaryDirectory() as runpath:
        mockplan = TestplanMock("plan", runpath=runpath)
        yield mockplan


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
