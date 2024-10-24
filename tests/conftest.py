"""Shared PyTest fixtures."""

import os
import shutil
import sys
import tempfile
from logging import Logger, INFO
from logging.handlers import RotatingFileHandler

sys.path.append(os.path.join(os.path.dirname(__file__), "helpers"))

import pytest

from testplan import TestplanMock
from testplan.common.utils.path import VAR_TMP


# Testplan and various drivers have a `runpath` attribute in their config
# and intermediate files will be placed under that path during running.
# In PyTest we can invoke fixtures such as `runpath`, `runpath_module` and
# `mockplan` so that a temporary `runpath` is generated. In order to easily
# collect the output an environment variable `TEST_ROOT_RUNPATH` can be set,
# it will be the parent directory of all those temporary `runpath`.


def _generate_runpath():
    """
    Generate a temporary directory unless specified by environment variable.
    """
    if os.environ.get("TEST_ROOT_RUNPATH"):
        dir = tempfile.TemporaryDirectory(dir=os.environ["TEST_ROOT_RUNPATH"])
        yield dir.name
        shutil.rmtree(dir.name, ignore_errors=True)
    else:
        parent_runpath = (
            VAR_TMP if os.name == "posix" and os.path.exists(VAR_TMP) else None
        )
        # The path will be automatically removed after the test
        dir = tempfile.TemporaryDirectory(dir=parent_runpath)
        yield dir.name
        shutil.rmtree(dir.name, ignore_errors=True)


# For `runpath` series fixtures, We were originally using a pytest builtin
# fixture called `tmp_path`, which will create a path in a form like:
# "/tmp/pytest-of-userid/pytest-151/test_sub_pub_unsub0", but it has a known
# issue: https://github.com/pytest-dev/pytest/issues/5456


@pytest.fixture(scope="function")
def runpath():
    """
    Return a temporary runpath for testing (function level).
    """
    yield from _generate_runpath()


@pytest.fixture(scope="class")
def runpath_class():
    """
    Return a temporary runpath for testing (class level).
    """
    yield from _generate_runpath()


@pytest.fixture(scope="module")
def runpath_module():
    """
    Return a temporary runpath for testing (module level).
    """
    yield from _generate_runpath()


@pytest.fixture(scope="function")
def mockplan(runpath):
    """
    Return a temporary TestplanMock for testing. Some components need a
    testplan as parent for getting runpath and configuration.
    """
    yield TestplanMock("plan", runpath=runpath)


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


class RotatingLogger(Logger):
    def __init__(self, path: str, name: str) -> None:
        super().__init__(name)
        self.path = path
        self.handler = RotatingFileHandler(
            path, maxBytes=10 * 1024, backupCount=5
        )
        self.addHandler(self.handler)

    @property
    def pattern(self):
        return f"{self.path}*"

    def doRollover(self):
        self.handler.doRollover()


@pytest.fixture
def rotating_logger(runpath):
    logpath = os.path.join(runpath, "test.log")
    logger = RotatingLogger(logpath, "TestLogger")
    yield logger

    logger.handler.close()


@pytest.fixture
def captplog(caplog):
    from testplan.common.utils.logger import TESTPLAN_LOGGER

    caplog.set_level(INFO)
    TESTPLAN_LOGGER.addHandler(caplog.handler)
    yield caplog
    TESTPLAN_LOGGER.removeHandler(caplog.handler)
