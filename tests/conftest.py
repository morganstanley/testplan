"""Shared PyTest fixtures."""

import os
import sys
import tempfile
from pathlib import Path
import inspect
from unittest.mock import patch

sys.path.append(os.path.join(os.path.dirname(__file__), "helpers"))

import pytest

from testplan import TestplanMock
from testplan.common.utils.path import VAR_TMP

import testplan.testing.multitest.result as result_py


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
        yield tempfile.mkdtemp(dir=os.environ["TEST_ROOT_RUNPATH"])
    else:
        parent_runpath = (
            VAR_TMP if os.name == "posix" and os.path.exists(VAR_TMP) else None
        )
        # The path will be automatically removed after the test
        with tempfile.TemporaryDirectory(dir=parent_runpath) as runpath:
            yield runpath


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


def get_hook():
    reference = result_py._bind_entry

    def track_and_call(entry, result_obj):
        va = inspect.stack()
        frame1, frame2, caller_frame, *_ = inspect.stack()

        # Test that frame1.filename and frame2.filename == result.py. Also that caller_frame.filename != result.py
        if not (Path(frame1.filename).name == Path(__file__).name and Path(frame2.filename).name == Path(
                __file__).name and
                Path(caller_frame.filename).name != Path(__file__).name):
            raise AssertionError('Location of _bind_entry function call breaks established pattern')
        assert False
        return reference(entry, result_obj)
    return track_and_call


def patch_bind_entry():
    replacement_hook = get_hook()
    patcher = patch.object(result_py, '_bind_entry', replacement_hook)
    patcher.start()


patch_bind_entry()
