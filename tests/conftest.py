"""Shared PyTest fixtures."""

import os

import pytest

import testplan
from testplan.common.utils import path


@pytest.fixture(scope="module")
def runpath():
    """
    Yield a temporary runpath for testing. The path will be automatically
    removed after the test.
    """
    with path.TemporaryDirectory() as runpath:
        yield runpath


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
