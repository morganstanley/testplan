"""Shared PyTest fixtures."""

import pytest

from testplan.common.utils import path


@pytest.fixture(scope="module")
def runpath():
    """
    Yield a temporary runpath for testing. The path will be automatically
    removed after the test.
    """
    with path.TemporaryDirectory() as runpath:
        yield runpath
